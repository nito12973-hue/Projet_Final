"""
Vues de l'Assistant SantéSN et du Support Administratif.

Gère l'interface conversationnelle patient (Assistant SantéSN),
l'ouverture et le suivi des demandes de support côté assuré,
et la gestion complète des tickets de support côté administrateur.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from ..forms import DemandeSupportForm, ReponseSupportForm
from ..models import DemandeSupport, JournalActivite, MessageSupport, Notification, User
from ..services.assistant import traiter_message_assistant
from .utils import _paginer, admin_required, journaliser, role_required


@role_required(User.Role.ASSURE)
def assistant_sante(request):
    """
    Interface conversationnelle de l'Assistant SantéSN pour les assurés.
    Supporte les requêtes classiques et les appels AJAX asynchrones (temps réel).
    """
    if request.GET.get("action") == "reset":
        request.session["assistant_conversation"] = []
        messages.info(request, "La conversation a été réinitialisée.")
        return redirect("assistant_sante")

    conversation = request.session.get("assistant_conversation", [])

    # Si c'est la toute première visite, injecter le message d'accueil
    if not conversation:
        reponse_accueil = traiter_message_assistant(request.user, "")
        conversation.append({
            "expediteur": "assistant",
            "texte": reponse_accueil["texte"],
            "type": reponse_accueil["type"],
            "actions": reponse_accueil.get("actions", []),
            "suggestions": reponse_accueil.get("suggestions", []),
            "date": timezone.now().strftime("%H:%M"),
        })
        request.session["assistant_conversation"] = conversation

    if request.method == "POST":
        is_ajax = (
            request.headers.get("x-requested-with") == "XMLHttpRequest"
            or request.GET.get("format") == "json"
            or request.content_type == "application/json"
        )
        message_texte = request.POST.get("message", "").strip()
        if not message_texte and request.body:
            try:
                import json
                payload = json.loads(request.body.decode("utf-8"))
                message_texte = (payload.get("message") or "").strip()
            except Exception:
                pass

        if not message_texte:
            if is_ajax:
                return JsonResponse({"success": False, "error": "Message vide."}, status=400)
            return redirect("assistant_sante")

        conversation.append({
            "expediteur": "patient",
            "texte": message_texte,
            "date": timezone.now().strftime("%H:%M"),
        })

        reponse = traiter_message_assistant(request.user, message_texte)

        conversation.append({
            "expediteur": "assistant",
            "texte": reponse["texte"],
            "type": reponse["type"],
            "actions": reponse.get("actions", []),
            "suggestions": reponse.get("suggestions", []),
            "date": timezone.now().strftime("%H:%M"),
        })

        # Plafond de l'historique en session (30 derniers messages max)
        if len(conversation) > 30:
            conversation = conversation[-30:]

        request.session["assistant_conversation"] = conversation

        # Si la requête est envoyée en AJAX depuis le navigateur
        if is_ajax:
            return JsonResponse({
                "success": True,
                "reponse": reponse,
                "date": timezone.now().strftime("%H:%M"),
            })

        return redirect("assistant_sante")

    return render(request, "assistant_sante.html", {
        "conversation": conversation,
    })


@role_required(User.Role.ASSURE)
def creer_demande_support(request):
    """Permet à un assuré de créer un ticket officiel d'assistance auprès de l'administration."""
    patient = getattr(request.user, "patient", None)

    if request.method == "POST":
        form = DemandeSupportForm(request.POST)
        if form.is_valid():
            demande = form.save(commit=False)
            demande.auteur = request.user
            demande.patient = patient
            demande.save()

            # Créer le premier message du fil
            premier_message = form.cleaned_data.get("premier_message", "").strip()
            MessageSupport.objects.create(
                demande=demande,
                auteur=request.user,
                message=premier_message,
            )

            # Notifier selon le rôle compétent :
            # - Si catégorie TECHNIQUE -> Administrateur informatique
            # - Si catégorie métier (PEC, RDV, Ordonnance, Famille) -> Gestionnaires de l'organisme de l'assuré
            nom_patient = request.user.get_full_name() or request.user.email
            if demande.categorie == DemandeSupport.Categorie.TECHNIQUE:
                destinataires = list(User.objects.filter(role=User.Role.ADMIN, is_active=True))
                titre_notif = "Nouvelle demande d'assistance informatique"
            else:
                org_id = patient.organisme_id if (patient and patient.organisme_id) else None
                if org_id:
                    destinataires = list(User.objects.filter(role=User.Role.GESTIONNAIRE, organisme_id=org_id, is_active=True))
                else:
                    destinataires = list(User.objects.filter(role=User.Role.GESTIONNAIRE, is_active=True))
                titre_notif = "Nouvelle demande d'assistance assuré"

            if destinataires:
                Notification.objects.bulk_create([
                    Notification(
                        destinataire=u,
                        titre=titre_notif,
                        message=f"L'assuré {nom_patient} a ouvert une demande ({demande.get_categorie_display()} - {demande.numero_dossier}) : {demande.objet}.",
                        type_evenement=Notification.TypeEvenement.SUPPORT_DEMANDE,
                        url_action=reverse("admin_detail_demande_support", args=[demande.pk]),
                    )
                    for u in destinataires
                ])

            messages.success(
                request,
                f"Votre demande d'assistance (dossier {demande.numero_dossier}) a été transmise avec succès à l'administration.",
                extra_tags="succes-critique"
            )
            return redirect("detail_demande_support", pk=demande.pk)
    else:
        # Pré-remplissage optionnel depuis l'assistant (ex: ?categorie=PEC&objet=Taux)
        initial = {}
        if request.GET.get("categorie") in DemandeSupport.Categorie.values:
            initial["categorie"] = request.GET.get("categorie")
        if request.GET.get("objet"):
            initial["objet"] = request.GET.get("objet")
        form = DemandeSupportForm(initial=initial)

    return render(request, "creer_demande_support.html", {"form": form})


@role_required(User.Role.ASSURE)
def mes_demandes_support(request):
    """Liste de toutes les demandes de support ouvertes par l'assuré."""
    demandes = DemandeSupport.objects.filter(auteur=request.user).order_by("-date_creation")

    statut_filtre = request.GET.get("statut", "")
    if statut_filtre in DemandeSupport.Statut.values:
        demandes = demandes.filter(statut=statut_filtre)

    return render(request, "mes_demandes_support.html", {
        "demandes": _paginer(request, demandes),
        "statut_filtre": statut_filtre,
        "statuts": DemandeSupport.Statut.choices,
    })


@role_required(User.Role.ASSURE)
def detail_demande_support(request, pk):
    """Détail d'une demande de support pour l'assuré, fil des échanges et ajout de réponse."""
    demande = get_object_or_404(DemandeSupport, pk=pk, auteur=request.user)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "cloturer":
            demande.statut = DemandeSupport.Statut.FERME
            demande.cloture_le = timezone.now()
            demande.cloture_par = request.user
            demande.save(update_fields=["statut", "cloture_le", "cloture_par", "date_mise_a_jour"])
            messages.success(request, f"La demande d'assistance (dossier {demande.numero_dossier}) a été clôturée avec succès.")
            return redirect("detail_demande_support", pk=demande.pk)

        # Ajout d'un nouveau message
        form = ReponseSupportForm(request.POST)
        if form.is_valid() and demande.statut != DemandeSupport.Statut.FERME:
            msg = form.save(commit=False)
            msg.demande = demande
            msg.auteur = request.user
            msg.save()

            # Passer le statut en EN_COURS ou EN_ATTENTE
            demande.statut = DemandeSupport.Statut.EN_ATTENTE
            demande.save(update_fields=["statut", "date_mise_a_jour"])

            # Notifier les responsables compétents
            nom_patient = request.user.get_full_name() or request.user.email
            if demande.categorie == DemandeSupport.Categorie.TECHNIQUE:
                destinataires = list(User.objects.filter(role=User.Role.ADMIN, is_active=True))
            else:
                org_id = demande.patient.organisme_id if (demande.patient and demande.patient.organisme_id) else None
                if org_id:
                    destinataires = list(User.objects.filter(role=User.Role.GESTIONNAIRE, organisme_id=org_id, is_active=True))
                else:
                    destinataires = list(User.objects.filter(role=User.Role.GESTIONNAIRE, is_active=True))

            if destinataires:
                Notification.objects.bulk_create([
                    Notification(
                        destinataire=u,
                        titre="Nouveau message sur demande d'assistance",
                        message=f"{nom_patient} a répondu sur la demande (dossier {demande.numero_dossier}).",
                        type_evenement=Notification.TypeEvenement.SUPPORT_DEMANDE,
                        url_action=reverse("admin_detail_demande_support", args=[demande.pk]),
                    )
                    for u in destinataires
                ])

            messages.success(request, "Votre message a été envoyé.")
            return redirect("detail_demande_support", pk=demande.pk)
    else:
        form = ReponseSupportForm()

    return render(request, "detail_demande_support.html", {
        "demande": demande,
        "messages_fil": demande.messages.select_related("auteur").order_by("date_envoi"),
        "form": form,
    })


@role_required(User.Role.ADMIN, User.Role.GESTIONNAIRE)
def admin_liste_demandes_support(request):
    """
    Gestion des tickets de support :
    - L'Administrateur accède à l'ensemble des tickets de la plateforme avec filtrage multi-critères.
    - Le Gestionnaire reçoit et traite les demandes administratives et santé de son propre organisme.
    """
    est_admin = (request.user.role == User.Role.ADMIN)
    demandes = DemandeSupport.objects.select_related("patient", "auteur", "patient__organisme").order_by("-date_creation")

    if est_admin:
        # L'administrateur système a une vision globale et peut filtrer par catégorie
        categories_disponibles = DemandeSupport.Categorie.choices
    else:
        # Le gestionnaire traite les demandes métier des assurés de sa structure
        if request.user.organisme_id:
            demandes = demandes.filter(patient__organisme_id=request.user.organisme_id)
        # Exclut les pures demandes informatiques système réservées à l'admin
        demandes = demandes.exclude(categorie=DemandeSupport.Categorie.TECHNIQUE)
        categories_disponibles = [
            (c, l) for c, l in DemandeSupport.Categorie.choices if c != DemandeSupport.Categorie.TECHNIQUE
        ]

    statut = request.GET.get("statut", "")
    if statut in DemandeSupport.Statut.values:
        demandes = demandes.filter(statut=statut)

    categorie = request.GET.get("categorie", "")
    if categorie in DemandeSupport.Categorie.values:
        demandes = demandes.filter(categorie=categorie)

    priorite = request.GET.get("priorite", "")
    if priorite in DemandeSupport.Priorite.values:
        demandes = demandes.filter(priorite=priorite)

    recherche = request.GET.get("q", "").strip()
    if recherche:
        demandes = demandes.filter(
            Q(numero_dossier__icontains=recherche)
            | Q(objet__icontains=recherche)
            | Q(auteur__email__icontains=recherche)
            | Q(auteur__first_name__icontains=recherche)
            | Q(auteur__last_name__icontains=recherche)
            | Q(patient__nom__icontains=recherche)
            | Q(patient__prenom__icontains=recherche)
        )

    contexte = {
        "demandes": _paginer(request, demandes),
        "statuts": DemandeSupport.Statut.choices,
        "categories": categories_disponibles,
        "priorites": DemandeSupport.Priorite.choices,
        "statut_choisi": statut,
        "categorie_choisie": categorie,
        "priorite_choisie": priorite,
        "recherche": recherche,
        "total_en_attente": demandes.filter(statut=DemandeSupport.Statut.EN_ATTENTE).count(),
        "est_admin": est_admin,
    }
    return render(request, "admin_liste_demandes_support.html", contexte)


@login_required
def admin_detail_demande_support(request, pk):
    """
    Traitement, réponse et clôture d'un ticket de support.
    Contrôle strict des accès :
    - L'Assuré est redirigé vers sa vue dédiée (detail_demande_support).
    - L'Admin accède à l'ensemble des tickets de support.
    - Le Gestionnaire ne peut accéder qu'aux tickets métier des assurés de son organisme.
    """
    if request.user.role == User.Role.ASSURE:
        return redirect("detail_demande_support", pk=pk)

    if request.user.role not in (User.Role.ADMIN, User.Role.GESTIONNAIRE):
        raise PermissionDenied

    est_admin = (request.user.role == User.Role.ADMIN)
    qs = DemandeSupport.objects.select_related("patient", "auteur", "patient__organisme")

    if est_admin:
        demande = get_object_or_404(qs, pk=pk)
    else:
        filtre = Q(patient__organisme_id=request.user.organisme_id) if request.user.organisme_id else Q()
        demande = get_object_or_404(
            qs.exclude(categorie=DemandeSupport.Categorie.TECHNIQUE).filter(filtre),
            pk=pk
        )

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "repondre":
            form = ReponseSupportForm(request.POST)
            if form.is_valid():
                msg = form.save(commit=False)
                msg.demande = demande
                msg.auteur = request.user
                msg.save()

                demande.statut = DemandeSupport.Statut.REPONDU
                demande.save(update_fields=["statut", "date_mise_a_jour"])

                # Notifier l'assuré auteur de la demande
                expediteur = "Support Technique Informatique" if est_admin else "Gestionnaire Santé / IPM"
                Notification.objects.create(
                    destinataire=demande.auteur,
                    titre=f"Réponse de l'{expediteur}",
                    message=f"Une réponse a été apportée à votre demande (dossier {demande.numero_dossier} : {demande.objet}).",
                    type_evenement=Notification.TypeEvenement.SUPPORT_REPONSE,
                    url_action=reverse("detail_demande_support", args=[demande.pk]),
                )

                journaliser(
                    request,
                    JournalActivite.Action.DECISION,
                    f"Support — Dossier {demande.numero_dossier}",
                    details=f"Réponse apportée à {demande.auteur.email} par {request.user.get_role_display()}"
                )

                messages.success(request, f"Votre réponse a été transmise avec succès à l'assuré (dossier {demande.numero_dossier}).")
                return redirect("admin_detail_demande_support", pk=demande.pk)

        elif action == "changer_statut":
            nouveau_statut = request.POST.get("nouveau_statut")
            if nouveau_statut in DemandeSupport.Statut.values:
                demande.statut = nouveau_statut
                if nouveau_statut == DemandeSupport.Statut.FERME:
                    demande.cloture_le = timezone.now()
                    demande.cloture_par = request.user
                demande.save()

                journaliser(
                    request,
                    JournalActivite.Action.MODIFICATION,
                    f"Support #{demande.numero_dossier}",
                    details=f"Statut changé en {demande.get_statut_display()}"
                )

                messages.success(request, f"Statut mis à jour : {demande.get_statut_display()}.")
                return redirect("admin_detail_demande_support", pk=demande.pk)
    else:
        form = ReponseSupportForm()

    return render(request, "admin_detail_demande_support.html", {
        "demande": demande,
        "messages_fil": demande.messages.select_related("auteur").order_by("date_envoi"),
        "form": form,
        "statuts": DemandeSupport.Statut.choices,
        "est_admin": est_admin,
    })
