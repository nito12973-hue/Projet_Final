"""
Espace Assuré : dashboard, profil, ayants droit, rendez-vous, ordonnances,
prises en charge, historique et navigation vers prestataires/médecins.
"""

import urllib.parse
from decimal import Decimal

from django.contrib import messages
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..forms import AyantDroitForm, ProfilAssureForm, RendezVousAssureForm
from ..models import (
    Consultation,
    JournalActivite,
    Medecin,
    Ordonnance,
    Patient,
    Prestataire,
    PriseEnCharge,
    RendezVous,
    User,
)
from .utils import _filtrer_rendez_vous, _paginer, journaliser, role_required


def _patient_principal(request):
    return getattr(request.user, "patient", None)


def _beneficiaires(patient):
    return Patient.objects.filter(
        Q(pk=patient.pk) | Q(assure_principal=patient)
    ).order_by("nom", "prenom")


def _distance_km(lat1, lon1, lat2, lon2):
    """Formule de Haversine : distance en km entre deux points GPS."""
    import math
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@role_required(User.Role.ASSURE)
def prestataires_proches(request):
    prestataires_partenaires = Prestataire.objects.filter(partenaire=True)
    avec_coordonnees = prestataires_partenaires.filter(
        latitude__isnull=False, longitude__isnull=False
    )
    sans_coordonnees = list(
        prestataires_partenaires.filter(
            Q(latitude__isnull=True) | Q(longitude__isnull=True)
        ).order_by("ville", "nom")
    )
    for prestataire in sans_coordonnees:
        morceaux = [valeur for valeur in (prestataire.nom, prestataire.ville) if valeur]
        prestataire.lien_itineraire = (
            "https://www.google.com/maps/dir/?api=1&destination="
            + urllib.parse.quote(", ".join(morceaux) + ", Senegal")
        )

    lat_param = request.GET.get("lat")
    lng_param = request.GET.get("lng")
    lat_utilisateur = lng_utilisateur = None
    if lat_param and lng_param:
        try:
            lat_utilisateur = float(lat_param)
            lng_utilisateur = float(lng_param)
        except ValueError:
            lat_utilisateur = lng_utilisateur = None
    localisation_active = lat_utilisateur is not None and lng_utilisateur is not None

    if localisation_active:
        prestataires_tries = sorted(
            (
                (prestataire, round(_distance_km(
                    lat_utilisateur, lng_utilisateur,
                    float(prestataire.latitude), float(prestataire.longitude),
                ), 1))
                for prestataire in avec_coordonnees
            ),
            key=lambda item: item[1],
        )
    else:
        prestataires_tries = [
            (prestataire, None)
            for prestataire in avec_coordonnees.order_by("ville", "nom")
        ]

    prestataires_geojson = [
        {
            "pk": prestataire.pk,
            "nom": prestataire.nom,
            "type": prestataire.get_type_prestataire_display(),
            "type_code": prestataire.type_prestataire,
            "ville": prestataire.ville,
            "telephone": prestataire.telephone,
            "latitude": float(prestataire.latitude),
            "longitude": float(prestataire.longitude),
            "medecin_count": prestataire.medecins.count(),
        }
        for prestataire in avec_coordonnees
    ]

    return render(request, "prestataires_proches.html", {
        "prestataires_tries": prestataires_tries,
        "prestataires_sans_coordonnees": sans_coordonnees,
        "prestataires_geojson": prestataires_geojson,
        "localisation_active": localisation_active,
    })


@role_required(User.Role.ASSURE)
def fiche_prestataire_assure(request, pk):
    """Fiche d'un prestataire et des medecins qui y exercent.

    Ce chainon manquait : l'ecran de proximite affichait deja le NOMBRE de
    medecins d'une structure, jamais lesquels. Le parcours prestataire ->
    medecin -> rendez-vous etait donc impossible a suivre.

    Restreint aux prestataires partenaires, comme la carte : une structure
    non conventionnee n'a pas a apparaitre dans un parcours de prise en
    charge.
    """
    prestataire = get_object_or_404(Prestataire, pk=pk, partenaire=True)
    medecins = prestataire.medecins.order_by("nom", "prenom")
    return render(request, "fiche_prestataire_assure.html", {
        "prestataire": prestataire,
        "medecins": medecins,
        "services": prestataire.services.order_by("nom"),
    })


@role_required(User.Role.ASSURE)
def fiche_medecin_assure(request, pk):
    """Profil d'un medecin, avec le bouton de demande de rendez-vous.

    On n'expose que des informations professionnelles (specialite,
    experience, presentation, structure, telephone) : aucune donnee sur ses
    patients ni sur ses consultations.
    """
    medecin = get_object_or_404(
        Medecin.objects.select_related("prestataire"), pk=pk
    )
    return render(request, "fiche_medecin_assure.html", {"medecin": medecin})


@role_required(User.Role.ASSURE)
def dashboard_assure(request):
    patient = _patient_principal(request)
    if patient is None:
        return redirect("mon_profil_assure")

    beneficiaires = _beneficiaires(patient)
    maintenant = timezone.now()
    rendez_vous_a_venir = RendezVous.objects.filter(
        patient__in=beneficiaires, date_heure__gte=maintenant
    ).exclude(statut=RendezVous.Statut.ANNULE)

    qr_svg = patient.qr_svg(
        request.build_absolute_uri(reverse("carte_scan", args=[patient.numero_carte])),
        taille_mm=75,
    )

    dernieres_prises_en_charge = PriseEnCharge.objects.filter(
        patient__in=beneficiaires
    ).select_related("patient").order_by("-date_demande")[:3]

    derniere_ordonnance = Ordonnance.objects.filter(
        consultation__patient__in=beneficiaires
    ).select_related("consultation__medecin", "consultation__patient").prefetch_related("lignes").order_by("-date_creation").first()

    prochains_rdv = list(
        rendez_vous_a_venir.select_related("medecin", "prestataire", "patient").order_by("date_heure")[:5]
    )

    contexte = {
        "patient": patient,
        "qr_svg": qr_svg,
        "total_ayants_droit": beneficiaires.exclude(pk=patient.pk).count(),
        "total_rendez_vous_a_venir": rendez_vous_a_venir.count(),
        "total_ordonnances": Ordonnance.objects.filter(consultation__patient__in=beneficiaires).count(),
        "prochain_rdv_principal": prochains_rdv[0] if prochains_rdv else None,
        "prochains_rendez_vous": prochains_rdv,
        "dernieres_prises_en_charge": dernieres_prises_en_charge,
        "derniere_ordonnance": derniere_ordonnance,
    }
    return render(request, "dashboard_assure.html", contexte)


@role_required(User.Role.ASSURE)
def mon_profil_assure(request):
    patient = _patient_principal(request)

    if request.method == "POST":
        form = ProfilAssureForm(request.POST, instance=patient)
        if form.is_valid():
            profil = form.save(commit=False)
            profil.user = request.user
            profil.type_beneficiaire = Patient.TypeBeneficiaire.PRINCIPAL
            profil.save()
            messages.success(request, "Profil enregistré.")
            return redirect("dashboard_assure")
    else:
        initial = {}
        if patient is None:
            initial = {"nom": request.user.last_name, "prenom": request.user.first_name}
        form = ProfilAssureForm(instance=patient, initial=initial)

    # Le QR du profil est EXACTEMENT celui de la carte : meme URL, meme
    # fabrique. Un second identifiant "pour le profil" serait un second
    # systeme a garder synchronise, donc a desynchroniser un jour.
    qr_svg = None
    if patient is not None:
        qr_svg = patient.qr_svg(
            request.build_absolute_uri(reverse("carte_scan", args=[patient.numero_carte])),
            taille_mm=52,
        )

    return render(request, "mon_profil_assure.html",
                  {"form": form, "patient": patient, "qr_svg": qr_svg})


@role_required(User.Role.ASSURE)
def liste_ayants_droit(request):
    patient = _patient_principal(request)
    if patient is None:
        return redirect("mon_profil_assure")
    return render(
        request,
        "liste_ayants_droit.html",
        {"ayants_droit": patient.ayants_droit.all().order_by("nom", "prenom")},
    )


@role_required(User.Role.ASSURE)
def ajouter_ayant_droit(request):
    patient = _patient_principal(request)
    if patient is None:
        return redirect("mon_profil_assure")

    if request.method == "POST":
        form = AyantDroitForm(request.POST)
        if form.is_valid():
            ayant_droit = form.save(commit=False)
            ayant_droit.type_beneficiaire = Patient.TypeBeneficiaire.AYANT_DROIT
            ayant_droit.assure_principal = patient
            ayant_droit.save()
            messages.success(request, "Ayant droit ajouté.")
            return redirect("liste_ayants_droit")
    else:
        form = AyantDroitForm()
    return render(request, "ajouter_ayant_droit.html", {"form": form})


@role_required(User.Role.ASSURE)
def modifier_ayant_droit(request, pk):
    patient = _patient_principal(request)
    if patient is None:
        return redirect("mon_profil_assure")
    ayant_droit = get_object_or_404(Patient, pk=pk, assure_principal=patient)

    if request.method == "POST":
        form = AyantDroitForm(request.POST, instance=ayant_droit)
        if form.is_valid():
            form.save()
            messages.success(request, "Ayant droit modifié.")
            return redirect("liste_ayants_droit")
    else:
        form = AyantDroitForm(instance=ayant_droit)
    return render(request, "modifier_ayant_droit.html", {"form": form, "ayant_droit": ayant_droit})


@role_required(User.Role.ASSURE)
def supprimer_ayant_droit(request, pk):
    patient = _patient_principal(request)
    if patient is None:
        return redirect("mon_profil_assure")
    ayant_droit = get_object_or_404(Patient, pk=pk, assure_principal=patient)

    if request.method == "POST":
        journaliser(request, JournalActivite.Action.SUPPRESSION, f"Ayant droit : {ayant_droit}",
                    f"rattaché à {patient}")
        ayant_droit.delete()
        messages.success(request, "Ayant droit supprimé.")
        return redirect("liste_ayants_droit")
    return render(
        request,
        "confirmer_suppression.html",
        {"objet": ayant_droit, "type": "Ayant droit"},
    )


@role_required(User.Role.ASSURE)
def mes_rendez_vous_assure(request):
    patient = _patient_principal(request)
    if patient is None:
        return redirect("mon_profil_assure")
    beneficiaires = _beneficiaires(patient)
    # L'ordre est pose par _filtrer_rendez_vous : paginer un queryset non
    # ordonne rend l'ordre des pages instable (et Django emet
    # UnorderedObjectListWarning).
    rendez_vous = RendezVous.objects.filter(patient__in=beneficiaires).select_related(
        "patient", "medecin", "prestataire"
    )
    rendez_vous, statut, periode = _filtrer_rendez_vous(request, rendez_vous)
    return render(request, "mes_rendez_vous.html", {
        "rendez_vous": _paginer(request, rendez_vous),
        "statut_choisi": statut,
        "periode_choisie": periode,
        "statuts": RendezVous.Statut.choices,
    })


@role_required(User.Role.ASSURE)
def ajouter_rendez_vous_assure(request):
    patient = _patient_principal(request)
    if patient is None:
        return redirect("mon_profil_assure")
    beneficiaires = _beneficiaires(patient)

    def _prestataire_demande(source):
        """Prestataire retenu, deduit du medecin s'il est fourni.

        Le parcours nominal arrive depuis la fiche d'un medecin : c'est LUI
        qui determine la structure, pas l'inverse. On ne fait donc confiance
        au parametre `prestataire` que si aucun medecin n'est designe.
        """
        medecin_id = source.get("medecin")
        if medecin_id and str(medecin_id).isdigit():
            medecin = Medecin.objects.filter(pk=medecin_id).first()
            if medecin is not None and medecin.prestataire_id:
                return medecin.prestataire
        prestataire_id = source.get("prestataire")
        if prestataire_id and str(prestataire_id).isdigit():
            return Prestataire.objects.filter(
                pk=prestataire_id, partenaire=True
            ).first()
        return None

    if request.method == "POST":
        form = RendezVousAssureForm(
            request.POST,
            beneficiaires=beneficiaires,
            prestataire=_prestataire_demande(request.POST),
        )
        if form.is_valid():
            rdv = form.save()
            from ..services.notifications import notifier_demande_rdv
            notifier_demande_rdv(rdv)
            messages.success(request, "Demande de rendez-vous envoyée.")
            return redirect("mes_rendez_vous_assure")
    else:
        prestataire = _prestataire_demande(request.GET)
        initial = {}
        if prestataire is not None:
            initial["prestataire"] = prestataire.pk
        medecin_id = request.GET.get("medecin")
        if medecin_id and medecin_id.isdigit():
            initial["medecin"] = medecin_id
        form = RendezVousAssureForm(
            beneficiaires=beneficiaires, prestataire=prestataire, initial=initial
        )
    return render(request, "ajouter_rendez_vous_assure.html", {"form": form})


@role_required(User.Role.ASSURE)
@require_POST
def annuler_rendez_vous_assure(request, pk):
    patient = _patient_principal(request)
    beneficiaires = _beneficiaires(patient) if patient else Patient.objects.none()
    rendez_vous = get_object_or_404(RendezVous, pk=pk, patient__in=beneficiaires)

    if rendez_vous.statut in (RendezVous.Statut.DEMANDE, RendezVous.Statut.CONFIRME):
        rendez_vous.statut = RendezVous.Statut.ANNULE
        rendez_vous.save(update_fields=["statut"])
        messages.success(request, "Rendez-vous annulé.")
    else:
        messages.error(request, "Ce rendez-vous ne peut plus être annulé.")
    return redirect("mes_rendez_vous_assure")


@role_required(User.Role.ASSURE)
def mes_ordonnances_assure(request):
    patient = _patient_principal(request)
    if patient is None:
        return redirect("mon_profil_assure")
    beneficiaires = _beneficiaires(patient)
    ordonnances = Ordonnance.objects.filter(
        consultation__patient__in=beneficiaires
    ).select_related(
        "consultation__patient", "consultation__medecin", "delivrance"
    ).order_by("-date_creation")

    # Meme filtre que la liste admin, pour la question inverse : l'assure
    # cherche ce qu'il PEUT ENCORE retirer, pas ce qu'on a oublie de retirer.
    delivrance = request.GET.get("delivrance", "")
    if delivrance == "non":
        ordonnances = ordonnances.filter(delivrance__isnull=True)
    elif delivrance == "oui":
        ordonnances = ordonnances.filter(delivrance__isnull=False)
    else:
        delivrance = ""

    return render(request, "mes_ordonnances.html", {
        "ordonnances": _paginer(request, ordonnances),
        "delivrance_choisie": delivrance,
    })


@role_required(User.Role.ASSURE)
def voir_ordonnance_assure(request, pk):
    from .medecin_espace import _contexte_ordonnance
    patient = _patient_principal(request)
    beneficiaires = _beneficiaires(patient) if patient else Patient.objects.none()
    ordonnance = get_object_or_404(
        Ordonnance.objects.select_related(
            "consultation__patient", "consultation__medecin__prestataire", "delivrance"),
        pk=pk, consultation__patient__in=beneficiaires)
    return render(request, "voir_ordonnance.html",
                  _contexte_ordonnance(request, ordonnance, "mes_ordonnances_assure"))


@role_required(User.Role.ASSURE)
def mes_prises_en_charge_assure(request):
    """Suivi par l'assure de ses prises en charge et de celles de ses ayants droit.

    Jusqu'ici l'assure voyait la CONSEQUENCE (sa part a payer, dans son
    historique) sans jamais voir la CAUSE : la demande existe-t-elle, ou en
    est-elle ? C'est pourtant ce statut qui determine s'il paie 10% ou 100%.

    Ce qui est affiche vient uniquement du modele : PriseEnCharge ne porte que
    patient, date, motif et statut. Les montants ne sont pas sur la prise en
    charge -- ils sont atteints par les consultations qui s'y rattachent
    (Consultation.prise_en_charge) et leur Paiement. Rien n'est invente :
    ni prestataire ni motif de refus n'existent dans le modele.
    """
    patient = _patient_principal(request)
    if patient is None:
        return redirect("mon_profil_assure")

    beneficiaires = _beneficiaires(patient)
    consultations = Consultation.objects.select_related(
        "medecin", "service", "paiement"
    ).order_by("-date_consultation")

    prises = (
        PriseEnCharge.objects
        .filter(patient__in=beneficiaires)
        .select_related("patient")
        .prefetch_related(Prefetch("consultation_set", queryset=consultations))
        .order_by("-date_demande")
    )

    statut = request.GET.get("statut", "")
    if statut:
        prises = prises.filter(statut=statut)

    page = _paginer(request, prises)

    # Totaux calcules apres pagination : seules les lignes affichees sont
    # parcourues, et les consultations sont deja prechargees.
    lignes = []
    for prise in page:
        rattachees = list(prise.consultation_set.all())
        a_charge = sum(
            (c.paiement.montant_part_patient for c in rattachees if hasattr(c, "paiement")),
            Decimal("0"),
        )
        couvert = sum(
            (c.paiement.montant_part_assurance for c in rattachees if hasattr(c, "paiement")),
            Decimal("0"),
        )
        lignes.append({
            "prise": prise,
            "consultations": rattachees,
            "montant_a_charge": a_charge,
            "montant_couvert": couvert,
        })

    return render(request, "mes_prises_en_charge.html", {
        "page": page,
        "lignes": lignes,
        "statut_choisi": statut,
        "statuts": PriseEnCharge.STATUT_CHOICES,
    })


@role_required(User.Role.ASSURE)
def mon_historique_assure(request):
    patient = _patient_principal(request)
    if patient is None:
        return redirect("mon_profil_assure")
    beneficiaires = _beneficiaires(patient)
    consultations = Consultation.objects.filter(patient__in=beneficiaires).select_related(
        "patient", "medecin", "service", "paiement"
    ).order_by("-date_consultation")
    return render(request, "mon_historique.html",
                  {"consultations": _paginer(request, consultations)})


@role_required(User.Role.ASSURE)
def carte_assure(request, pk=None):
    """Carte de prise en charge dématérialisée pour l'assuré et ses ayants droit."""
    patient_assure = _patient_principal(request)
    if patient_assure is None:
        return redirect("mon_profil_assure")

    if pk is not None:
        patient = get_object_or_404(
            Patient.objects.select_related("assure_principal", "plan_couverture"), pk=pk
        )
        if patient.pk != patient_assure.pk and patient.assure_principal_id != patient_assure.pk:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Vous n'êtes pas autorisé à consulter cette carte.")
    else:
        patient = patient_assure

    url_scan = request.build_absolute_uri(
        reverse("carte_scan", args=[patient.numero_carte])
    )

    journaliser(request, JournalActivite.Action.CARTE, f"Carte de {patient}",
                f"n° {patient.numero_carte}")

    return render(request, "carte_patient.html", {
        "patient": patient,
        "qr_svg": patient.qr_svg(url_scan),
        "url_scan": url_scan,
    })

