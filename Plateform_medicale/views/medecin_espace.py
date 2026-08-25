"""
Espace Médecin : dashboard, agenda, gestion des patients, consultations,
ordonnances et profil.
"""

import datetime

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Case, IntegerField, Q, Value, When
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..forms import ConsultationForm, LigneOrdonnanceFormSet, MedecinProfilForm
from ..models import (
    Consultation,
    Medecin,
    Ordonnance,
    Paiement,
    Patient,
    RendezVous,
    User,
)
from .utils import _filtrer_rendez_vous, _paginer, journaliser, role_required
from .dashboard import _consultations_par_jour


def _medecin_courant(request):
    return getattr(request.user, "medecin", None)


def _patients_du_medecin(medecin):
    return Patient.objects.filter(
        Q(rendez_vous__medecin=medecin) | Q(consultation__medecin=medecin)
    ).distinct().order_by("nom", "prenom")


@role_required(User.Role.MEDECIN)
def dashboard_medecin(request):
    medecin = _medecin_courant(request)
    if medecin is None:
        return render(request, "medecin_fiche_manquante.html")

    maintenant = timezone.now()
    aujourd_hui = maintenant.date()

    demandes_en_attente = RendezVous.objects.filter(
        medecin=medecin, statut=RendezVous.Statut.DEMANDE
    ).select_related("patient").order_by("date_heure")

    rendez_vous_du_jour = RendezVous.objects.filter(
        medecin=medecin, date_heure__date=aujourd_hui
    ).exclude(statut=RendezVous.Statut.ANNULE).select_related("patient").order_by("date_heure")

    derniers_patients = Consultation.objects.filter(
        medecin=medecin
    ).select_related("patient").order_by("-date_consultation")[:4]

    dernieres_ordonnances = Ordonnance.objects.filter(
        consultation__medecin=medecin
    ).select_related("consultation__patient").prefetch_related("lignes").order_by("-date_creation")[:4]

    contexte = {
        "medecin": medecin,
        "nb_demandes_en_attente": demandes_en_attente.count(),
        "demandes_en_attente": demandes_en_attente[:3],
        "rendez_vous_du_jour": rendez_vous_du_jour,
        "total_rendez_vous_du_jour": rendez_vous_du_jour.count(),
        "total_patients": _patients_du_medecin(medecin).count(),
        "total_consultations": Consultation.objects.filter(medecin=medecin).count(),
        "total_ordonnances": Ordonnance.objects.filter(consultation__medecin=medecin).count(),
        "derniers_patients": derniers_patients,
        "dernieres_ordonnances": dernieres_ordonnances,
    }
    return render(request, "dashboard_medecin.html", contexte)


@role_required(User.Role.MEDECIN)
def agenda_medecin(request):
    medecin = _medecin_courant(request)
    if medecin is None:
        return render(request, "medecin_fiche_manquante.html")

    # L'ordre est pose par _filtrer_rendez_vous (il depend de la periode
    # demandee) : un queryset pagine doit toujours etre ordonne.
    rendez_vous = RendezVous.objects.filter(medecin=medecin).select_related(
        "patient", "prestataire"
    )
    rendez_vous, statut, periode = _filtrer_rendez_vous(request, rendez_vous)
    return render(request, "agenda_medecin.html", {
        "rendez_vous": _paginer(request, rendez_vous),
        "statut_choisi": statut,
        "periode_choisie": periode,
        "statuts": RendezVous.Statut.choices,
    })


@role_required(User.Role.MEDECIN)
@require_POST
def changer_statut_rendez_vous(request, pk):
    medecin = _medecin_courant(request)
    rendez_vous = get_object_or_404(RendezVous, pk=pk, medecin=medecin)
    nouveau_statut = request.POST.get("statut")
    if nouveau_statut in RendezVous.Statut.values:
        rendez_vous.statut = nouveau_statut
        rendez_vous.save(update_fields=["statut"])
        from ..services.notifications import notifier_confirmation_rdv, notifier_refus_rdv
        if nouveau_statut == RendezVous.Statut.CONFIRME:
            notifier_confirmation_rdv(rendez_vous)
        elif nouveau_statut == RendezVous.Statut.REFUSE:
            notifier_refus_rdv(rendez_vous)
        messages.success(request, "Statut du rendez-vous mis à jour.")
    return redirect("agenda_medecin")


@role_required(User.Role.MEDECIN)
def mes_patients(request):
    medecin = _medecin_courant(request)
    if medecin is None:
        return render(request, "medecin_fiche_manquante.html")
    # Pas de barre de filtres ici : la page porte deja une recherche
    # ("Recherche rapide", combobox JS sur rechercher_patients_medecin) qui
    # ouvre directement la fiche du patient. Un second champ de recherche sur
    # le meme ecran serait un doublon, pas une fonctionnalite.
    return render(request, "mes_patients.html",
                  {"patients": _paginer(request, _patients_du_medecin(medecin))})


@role_required(User.Role.MEDECIN)
def rechercher_patients_medecin(request):
    """
    Recherche live pour la barre de recherche rapide du medecin (numero de
    carte, nom, prenom, identifiant numerique). Renvoie du JSON, jamais de
    donnee medicale : seulement de quoi identifier le bon patient avant
    d'ouvrir sa fiche (voir fiche_patient_medecin).
    """
    medecin = _medecin_courant(request)
    if medecin is None:
        return JsonResponse({"resultats": []})

    requete = request.GET.get("q", "").strip()
    if len(requete) < 2:
        return JsonResponse({"resultats": []})

    filtre = (
        Q(numero_carte__icontains=requete)
        | Q(nom__icontains=requete)
        | Q(prenom__icontains=requete)
    )
    if requete.isdecimal():
        filtre |= Q(pk=requete)

    patients = list(
        Patient.objects.filter(filtre)
        .annotate(
            priorite=Case(
                When(numero_carte__iexact=requete, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by("priorite", "nom", "prenom")[:8]
    )

    patients_lies = set(
        _patients_du_medecin(medecin)
        .filter(pk__in=[patient.pk for patient in patients])
        .values_list("pk", flat=True)
    )

    resultats = [
        {
            "id": patient.pk,
            "nom": patient.nom,
            "prenom": patient.prenom,
            "numero_carte": patient.numero_carte,
            "type_beneficiaire": patient.get_type_beneficiaire_display(),
            "date_naissance": patient.date_naissance.isoformat(),
            "deja_vu": patient.pk in patients_lies,
        }
        for patient in patients
    ]
    return JsonResponse({"resultats": resultats})


@role_required(User.Role.MEDECIN)
def fiche_patient_medecin(request, pk):
    """
    Fiche d'un patient, ouverte depuis la recherche rapide. L'historique
    n'expose que les consultations du medecin connecte avec ce patient
    (jamais celles d'un autre medecin - voir la spec, section "Decisions
    actees").
    """
    medecin = _medecin_courant(request)
    if medecin is None:
        return render(request, "medecin_fiche_manquante.html")

    patient = get_object_or_404(
        Patient.objects.select_related(
            "assure_principal", "assure_principal__plan_couverture", "plan_couverture"
        ),
        pk=pk,
    )
    historique = (
        Consultation.objects.filter(medecin=medecin, patient=patient)
        .select_related("service", "prise_en_charge")
        .prefetch_related("ordonnances")
        .order_by("-date_consultation")
    )
    if patient.type_beneficiaire == Patient.TypeBeneficiaire.PRINCIPAL:
        ayants_droit = patient.ayants_droit.all()
    else:
        ayants_droit = Patient.objects.none()

    prochains_rendez_vous = (
        RendezVous.objects.filter(medecin=medecin, patient=patient, date_heure__gte=timezone.now())
        .exclude(statut=RendezVous.Statut.ANNULE)
        .order_by("date_heure")
    )

    contexte = {
        "patient": patient,
        "historique": historique,
        "ayants_droit": ayants_droit,
        "prochains_rendez_vous": prochains_rendez_vous,
        "deja_vu": _patients_du_medecin(medecin).filter(pk=patient.pk).exists(),
    }
    return render(request, "fiche_patient_medecin.html", contexte)


@role_required(User.Role.MEDECIN)
def historique_consultations(request):
    medecin = _medecin_courant(request)
    if medecin is None:
        return render(request, "medecin_fiche_manquante.html")

    consultations = Consultation.objects.filter(medecin=medecin).select_related(
        "patient", "service", "prise_en_charge"
    ).prefetch_related("ordonnances").order_by("-date_consultation")

    patient_id = request.GET.get("patient", "")
    if patient_id.isdigit():
        consultations = consultations.filter(patient_id=patient_id)

    date_filtre = request.GET.get("date", "")
    if date_filtre:
        try:
            date_valide = datetime.date.fromisoformat(date_filtre)
        except ValueError:
            date_filtre = ""
        else:
            consultations = consultations.filter(date_consultation__date=date_valide)

    contexte = {
        "consultations": _paginer(request, consultations),
        "patients_du_medecin": _patients_du_medecin(medecin),
        "patient_selectionne": patient_id,
        "date_selectionnee": date_filtre,
    }
    return render(request, "historique_consultations.html", contexte)


@role_required(User.Role.MEDECIN)
def ajouter_consultation_medecin(request):
    medecin = _medecin_courant(request)
    if medecin is None:
        return render(request, "medecin_fiche_manquante.html")

    rdv_id = request.GET.get("rdv_id") or request.POST.get("rdv_id")
    rdv = None
    if rdv_id and str(rdv_id).isdigit():
        rdv = get_object_or_404(RendezVous, pk=rdv_id, medecin=medecin)

    if request.method == "POST":
        form = ConsultationForm(request.POST)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.medecin = medecin
            consultation.save()
            Paiement.calculer_pour(consultation).save()
            if rdv:
                rdv.statut = RendezVous.Statut.TERMINE
                rdv.save(update_fields=["statut"])
            messages.success(request, "Consultation enregistrée avec succès.")
            return redirect("ajouter_ordonnance_medecin", consultation_pk=consultation.pk)
    else:
        patient_id = request.GET.get("patient", "")
        initial = {}
        if rdv:
            initial["patient"] = rdv.patient_id
            initial["date_consultation"] = timezone.now()
        elif patient_id.isdecimal() and Patient.objects.filter(pk=patient_id).exists():
            initial["patient"] = patient_id
        form = ConsultationForm(initial=initial)
    return render(request, "ajouter_consultation_medecin.html", {"form": form, "rdv": rdv})


@role_required(User.Role.MEDECIN)
def ajouter_ordonnance_medecin(request, consultation_pk):
    medecin = _medecin_courant(request)
    consultation = get_object_or_404(Consultation, pk=consultation_pk, medecin=medecin)

    # Ordonnance STRUCTUREE : le medecin saisit des lignes, plus du texte
    # libre. medicaments reste vide pour les nouvelles ordonnances -- il ne
    # porte que le contenu des ordonnances anterieures a LigneOrdonnance.
    #
    # Il n'existe PAS de modification d'ordonnance dans SantéSN : seule la
    # creation. Ne pas en inventer une ici -- ce serait une regle metier
    # nouvelle, decidee au passage.
    if request.method == "POST":
        ordonnance = Ordonnance(consultation=consultation)
        formset = LigneOrdonnanceFormSet(request.POST, instance=ordonnance)
        if formset.is_valid():
            with transaction.atomic():
                ordonnance.save()
                lignes = formset.save(commit=False)
                # L'ordre suit la saisie : la premiere ligne remplie est la
                # premiere prescrite.
                for rang, ligne in enumerate(lignes, start=1):
                    ligne.ordre = rang
                    ligne.save()
                for supprimee in formset.deleted_objects:
                    supprimee.delete()
            from ..services.notifications import notifier_ordonnance_creee
            notifier_ordonnance_creee(ordonnance)
            messages.success(request, "Ordonnance créée.", extra_tags="succes-critique")
            return redirect("voir_ordonnance_medecin", pk=ordonnance.pk)
    else:
        formset = LigneOrdonnanceFormSet(instance=Ordonnance())

    return render(
        request,
        "ajouter_ordonnance_medecin.html",
        {"formset": formset, "consultation": consultation},
    )


def _contexte_ordonnance(request, ordonnance, retour_url):
    """Contexte commun aux deux vues d'ordonnance (medecin et assure).

    DEUX FORMATS, JAMAIS MELANGES :

      - ordonnance STRUCTUREE (elle a des LigneOrdonnance) : on rend le
        tableau medicament / dosage / posologie / duree / quantite ;
      - ordonnance HISTORIQUE (texte libre, anterieure a LigneOrdonnance) :
        on rend ses lignes de texte telles qu'elles ont ete saisies.

    Aucune conversion de l'une vers l'autre : le texte des anciennes
    ordonnances contient au moins trois formats, dont des tableaux tapes a
    la main. Le decouper automatiquement finirait par attribuer un dosage au
    mauvais medicament, sur des ordonnances deja delivrees.

    Le QR encode l'adresse de verification de l'ordonnance, pas les
    medicaments : le contenu medical ne quitte jamais le serveur.
    """
    lignes_structurees = list(ordonnance.lignes.all())
    return {
        "ordonnance": ordonnance,
        "retour_url": retour_url,
        "lignes_structurees": lignes_structurees,
        # Rendu historique : uniquement si aucune ligne structuree n'existe.
        "lignes_prescription": [] if lignes_structurees else [
            ligne.strip() for ligne in ordonnance.medicaments.splitlines()
            if ligne.strip()
        ],
        "qr_svg": ordonnance.qr_svg,
    }


@role_required(User.Role.MEDECIN)
def voir_ordonnance_medecin(request, pk):
    medecin = _medecin_courant(request)
    ordonnance = get_object_or_404(
        Ordonnance.objects.select_related(
            "consultation__patient", "consultation__medecin__prestataire", "delivrance"),
        pk=pk, consultation__medecin=medecin)
    return render(request, "voir_ordonnance.html",
                  _contexte_ordonnance(request, ordonnance, "historique_consultations"))


@role_required(User.Role.MEDECIN)
def modifier_profil_medecin(request):
    medecin = _medecin_courant(request)
    if medecin is None:
        return render(request, "medecin_fiche_manquante.html")

    if request.method == "POST":
        form = MedecinProfilForm(request.POST, instance=medecin)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour.")
            return redirect("modifier_profil_medecin")
    else:
        form = MedecinProfilForm(instance=medecin)
    return render(request, "modifier_profil_medecin.html", {"form": form, "medecin": medecin})


@role_required(User.Role.MEDECIN)
def liste_ordonnances(request):
    """Liste des ordonnances du medecin connecte."""
    medecin = _medecin_courant(request)
    if medecin is None:
        return render(request, "medecin_fiche_manquante.html")
    from django.db.models import Q
    ordonnances = Ordonnance.objects.filter(consultation__medecin=medecin).select_related(
        "consultation__patient", "delivrance"
    ).order_by("-date_creation")
    return render(request, "liste_ordonnances_medecin.html", {
        "ordonnances": _paginer(request, ordonnances),
    })


@role_required(User.Role.MEDECIN)
@require_POST
def annuler_ordonnance_medecin(request, pk):
    """Annule une ordonnance émise par le médecin connecté si elle n'est pas encore délivrée."""
    medecin = _medecin_courant(request)
    if medecin is None:
        return render(request, "medecin_fiche_manquante.html")

    ordonnance = get_object_or_404(
        Ordonnance.objects.select_related("consultation__medecin", "consultation__patient"),
        pk=pk,
        consultation__medecin=medecin,
    )

    if ordonnance.est_delivree:
        messages.error(request, "Cette ordonnance a déjà été délivrée en pharmacie.")
        return redirect("voir_ordonnance_medecin", pk=pk)

    motif = request.POST.get("motif_annulation", "").strip()
    if not motif:
        messages.error(request, "Veuillez indiquer un motif d'annulation.")
        return redirect("voir_ordonnance_medecin", pk=pk)

    ordonnance.annuler(motif=motif)

    journaliser(
        request,
        action="MODIFICATION",
        objet=f"Ordonnance #{ordonnance.code_qr}",
        details=f"Annulation par le médecin. Motif : {motif}",
    )

    messages.success(request, f"Ordonnance #{ordonnance.code_qr} annulée.")
    return redirect("voir_ordonnance_medecin", pk=pk)

