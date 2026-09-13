"""
Vues de l'Assistant SantéSN et du Support Administratif.

Gère l'interface conversationnelle patient (Assistant SantéSN),
l'ouverture et le suivi des demandes de support côté assuré,
et la gestion complète des tickets de support côté administrateur.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

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

            # Notifier tous les administrateurs actifs
            admins = list(User.objects.filter(role=User.Role.ADMIN, is_active=True))
            if admins:
                nom_patient = request.user.get_full_name() or request.user.email
                Notification.objects.bulk_create([
                    Notification(
                        destinataire=admin,
                        titre="Nouvelle demande d'assistance",
                        message=f"L'assuré {nom_patient} a ouvert le ticket #{demande.numero_dossier} : {demande.objet}.",
                        type_evenement=Notification.TypeEvenement.SUPPORT_DEMANDE,
                        url_action=reverse("admin_detail_demande_support", args=[demande.pk]),
                    )
                    for admin in admins
                ])

            messages.success(
                request,
                f"Votre demande #{demande.numero_dossier} a été transmise avec succès à l'administration.",
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
            messages.success(request, f"La demande #{demande.numero_dossier} a été clôturée.")
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

            # Notifier les administrateurs
            admins = list(User.objects.filter(role=User.Role.ADMIN, is_active=True))
            if admins:
                nom_patient = request.user.get_full_name() or request.user.email
                Notification.objects.bulk_create([
                    Notification(
                        destinataire=admin,
                        titre="Nouveau message sur demande support",
                        message=f"{nom_patient} a répondu sur le ticket #{demande.numero_dossier}.",
                        type_evenement=Notification.TypeEvenement.SUPPORT_DEMANDE,
                        url_action=reverse("admin_detail_demande_support", args=[demande.pk]),
                    )
                    for admin in admins
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


@admin_required
def admin_liste_demandes_support(request):
    """Vue administrateur : Liste de toutes les demandes de support avec filtres avancés."""
    demandes = DemandeSupport.objects.select_related("patient", "auteur").order_by("-date_creation")

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
        "categories": DemandeSupport.Categorie.choices,
        "priorites": DemandeSupport.Priorite.choices,
        "statut_choisi": statut,
        "categorie_choisie": categorie,
        "priorite_choisie": priorite,
        "recherche": recherche,
        "total_en_attente": DemandeSupport.objects.filter(statut=DemandeSupport.Statut.EN_ATTENTE).count(),
    }
    return render(request, "admin_liste_demandes_support.html", contexte)


@admin_required
def admin_detail_demande_support(request, pk):
    """Vue administrateur : Traitement, réponse et clôture d'un ticket de support patient."""
    demande = get_object_or_404(DemandeSupport.objects.select_related("patient", "auteur"), pk=pk)

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
                Notification.objects.create(
                    destinataire=demande.auteur,
                    titre="Réponse de l'administration SantéSN",
                    message=f"L'administration a répondu à votre demande #{demande.numero_dossier} ({demande.objet}).",
                    type_evenement=Notification.TypeEvenement.SUPPORT_REPONSE,
                    url_action=reverse("detail_demande_support", args=[demande.pk]),
                )

                journaliser(
                    request,
                    JournalActivite.Action.DECISION,
                    f"Support #{demande.numero_dossier}",
                    details=f"Réponse apportée à {demande.auteur.email}"
                )

                messages.success(request, f"Réponse transmise à l'assuré pour la demande #{demande.numero_dossier}.")
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
    })
