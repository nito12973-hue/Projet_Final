"""CRUD Patients (liste, ajout, modification, suppression) + carte de prise en charge."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..forms import PatientCreationForm, PatientForm, generer_mot_de_passe
from ..models import JournalActivite, Notification, Patient, User
from ..services.notifications import emettre_notification
from ..services.onboarding import construire_bilan_onboarding, envoyer_activation_utilisateur
from .utils import _avertissement_cascade, _paginer, _trier, admin_required, journaliser
from .medecin_espace import _medecin_courant


@admin_required
def liste_patients(request):
    patients = Patient.objects.select_related("assure_principal", "plan_couverture", "user").all()

    recherche = request.GET.get("q", "").strip()
    if recherche:
        patients = patients.filter(
            Q(nom__icontains=recherche)
            | Q(prenom__icontains=recherche)
            | Q(numero_carte__icontains=recherche)
            | Q(telephone__icontains=recherche)
            | Q(user__email__icontains=recherche)
        )

    type_beneficiaire = request.GET.get("type", "")
    if type_beneficiaire:
        patients = patients.filter(type_beneficiaire=type_beneficiaire)

    statut_validation = request.GET.get("statut", "")
    if statut_validation:
        patients = patients.filter(statut_validation=statut_validation)

    nb_en_attente = Patient.objects.filter(
        type_beneficiaire=Patient.TypeBeneficiaire.AYANT_DROIT,
        statut_validation=Patient.StatutValidation.EN_ATTENTE,
    ).count()

    patients = _trier(
        request, patients,
        ["id", "nom", "type_beneficiaire", "assure_principal__nom", "numero_carte", "plan_couverture__nom", "statut_validation"],
        ["nom", "prenom"],
    )

    contexte = {
        "patients": _paginer(request, patients),
        "types_beneficiaire": Patient.TypeBeneficiaire.choices,
        "type_selectionne": type_beneficiaire,
        "statuts_validation": Patient.StatutValidation.choices,
        "statut_selectionne": statut_validation,
        "nb_en_attente": nb_en_attente,
        "recherche": recherche,
    }
    return render(request, "liste_patients.html", contexte)


@admin_required
def ajouter_patient(request):
    if request.method == "POST":
        form = PatientCreationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                patient = form.save(commit=False)
                if patient.type_beneficiaire == Patient.TypeBeneficiaire.PRINCIPAL:
                    mot_de_passe = generer_mot_de_passe()
                    utilisateur = User.objects.create_user(
                        email=form.cleaned_data['email'],
                        password=mot_de_passe,
                        role=User.Role.ASSURE,
                        first_name=patient.prenom,
                        last_name=patient.nom,
                        phone_number=patient.telephone,
                    )
                    patient.user = utilisateur
                    patient.save()
                    statut_onboarding = envoyer_activation_utilisateur(utilisateur, request=request)
                    journaliser(request, JournalActivite.Action.CREATION, f"Assuré {utilisateur.email}", f"{patient.prenom} {patient.nom}")
                    bilan = statut_onboarding.get("bilan") or construire_bilan_onboarding(statut_onboarding, utilisateur, action="creation")
                    if bilan["niveau"] == "success":
                        messages.success(request, bilan["texte_flash"])
                    else:
                        messages.warning(request, bilan["texte_flash"])
                    return redirect("liste_patients")
                patient.save()
                journaliser(request, JournalActivite.Action.CREATION, f"Ayant droit {patient}", f"Rattaché à {patient.assure_principal}")
                messages.success(request, "Assuré ajouté.")
                return redirect("liste_patients")
    else:
        form = PatientCreationForm()
    return render(request, "ajouter_patient.html", {"form": form})


@admin_required
def modifier_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == "POST":
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, "Assuré modifié.")
            return redirect("liste_patients")
    else:
        form = PatientForm(instance=patient)
    return render(request, "modifier_patient.html", {"form": form, "patient": patient})


@admin_required
def supprimer_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    nb_consultations = patient.consultation_set.count()
    nb_prises_en_charge = patient.priseencharge_set.count()
    est_protege = (nb_consultations > 0 or nb_prises_en_charge > 0)

    if request.method == "POST":
        if est_protege:
            messages.error(
                request,
                f"Impossible de supprimer le dossier de {patient} : {nb_consultations} consultation(s) "
                f"et {nb_prises_en_charge} prise(s) en charge y sont associées. "
                "Conformément à la réglementation sur la santé et la traçabilité des soins, un dossier comportant un historique médical actif ne peut pas être supprimé.",
            )
            return redirect("liste_patients")

        try:
            with transaction.atomic():
                user_associe = patient.user
                nom_patient = str(patient)
                details_journal = "compte de connexion désactivé" if user_associe else "sans compte de connexion"

                if user_associe:
                    user_associe.is_active = False
                    user_associe.save(update_fields=["is_active"])

                patient.delete()

                # Journalisation APRES la suppression effective
                journaliser(
                    request,
                    JournalActivite.Action.SUPPRESSION,
                    f"Assuré : {nom_patient}",
                    details_journal,
                )
                messages.success(request, f"Assuré {nom_patient} supprimé avec succès.")
                return redirect("liste_patients")
        except ProtectedError:
            messages.error(
                request,
                f"Impossible de supprimer le dossier de {patient} : des actes médicaux protégés y sont rattachés.",
            )
            return redirect("liste_patients")

    avertissement = _avertissement_cascade({
        "ayant(s) droit": patient.ayants_droit.count(),
        "consultation(s)": nb_consultations,
        "prise(s) en charge": nb_prises_en_charge,
        "rendez-vous": patient.rendez_vous.count(),
    })
    return render(
        request,
        "confirmer_suppression.html",
        {
            "objet": patient,
            "type": "Patient",
            "avertissement": avertissement,
            "est_protege": est_protege,
            "motif_blocage": (
                "Ce patient possède des consultations médicales ou des prises en charge enregistrées. "
                "Pour garantir la traçabilité médico-légale et la conformité CDP, la suppression de ce dossier est bloquée."
            ) if est_protege else None,
        },
    )


@login_required
@admin_required
def carte_patient(request, pk):
    """Carte de prise en charge, recto/verso, prete a imprimer."""
    patient = get_object_or_404(
        Patient.objects.select_related("assure_principal", "plan_couverture"), pk=pk
    )

    url_scan = request.build_absolute_uri(
        reverse("carte_scan", args=[patient.numero_carte])
    )

    # Editer une carte, c'est delivrer une piece : on trace qui et pour qui.
    journaliser(request, JournalActivite.Action.CARTE, f"Carte de {patient}",
                f"n° {patient.numero_carte}")

    return render(request, "carte_patient.html", {
        "patient": patient,
        "qr_svg": patient.qr_svg(url_scan),
        "url_scan": url_scan,
    })


from .utils import role_required  # noqa: E402


@role_required(User.Role.MEDECIN, User.Role.PHARMACIEN)
def carte_scan(request, numero):
    """Page ouverte en scannant le QR d'une carte de prise en charge.

    LE QR NE DONNE AUCUN DROIT. Il ouvre une adresse ; c'est le decorateur
    ci-dessus qui protege : un visiteur non connecte est renvoye vers la
    connexion, un assure ou un administrateur recoit un 403. Le numero de
    carte n'est pas un secret (il est imprime sur la carte elle-meme), il ne
    pouvait donc pas servir de cle.

    Ce que chaque role voit est volontairement different :

      PHARMACIEN : uniquement les ordonnances NON DELIVREES.

      MEDECIN : uniquement les ordonnances issues de SES PROPRES consultations.
    """
    from ..models import Ordonnance
    patient = get_object_or_404(
        Patient.objects.select_related("assure_principal", "plan_couverture"),
        numero_carte=numero)

    # Sécurité Anti-Fraude : carte inactive si en attente de validation ou refusée
    if not patient.est_valide:
        return render(request, "carte_scan.html", {
            "patient": patient,
            "ordonnances": [],
            "carte_inactive": True,
            "statut_validation": patient.get_statut_validation_display(),
        })

    ordonnances = (
        Ordonnance.objects
        .filter(consultation__patient=patient)
        .select_related("consultation__medecin", "consultation__service", "delivrance")
        .order_by("-date_creation")
    )

    if request.user.role == User.Role.PHARMACIEN:
        ordonnances = ordonnances.filter(delivrance__isnull=True)
        portee = "Ordonnances en attente de délivrance"
    else:
        medecin = _medecin_courant(request)
        if medecin is None:
            return render(request, "medecin_fiche_manquante.html")
        ordonnances = ordonnances.filter(consultation__medecin=medecin)
        portee = "Ordonnances issues de vos consultations"

    return render(request, "carte_scan.html", {
        "patient": patient,
        "ordonnances": _paginer(request, ordonnances),
        "portee": portee,
        "carte_inactive": False,
    })


@admin_required
@require_POST
def valider_ayant_droit(request, pk):
    ayant_droit = get_object_or_404(
        Patient.objects.select_related("assure_principal__user"),
        pk=pk,
        type_beneficiaire=Patient.TypeBeneficiaire.AYANT_DROIT,
    )
    ayant_droit.statut_validation = Patient.StatutValidation.VALIDE
    ayant_droit.date_decision = timezone.now()
    ayant_droit.valide_par = request.user
    ayant_droit.motif_refus = ""
    ayant_droit.save(update_fields=["statut_validation", "date_decision", "valide_par", "motif_refus"])

    journaliser(
        request,
        JournalActivite.Action.DECISION,
        str(ayant_droit),
        f"Validation de l'ayant droit {ayant_droit} (assuré : {ayant_droit.assure_principal})",
    )

    if ayant_droit.assure_principal and ayant_droit.assure_principal.user:
        emettre_notification(
            destinataire=ayant_droit.assure_principal.user,
            type_evenement=Notification.TypeEvenement.AYANT_DROIT_VALIDE,
            titre="Ayant droit validé par l'IPM",
            message=(
                f"La demande de rattachement pour {ayant_droit.prenom} {ayant_droit.nom} "
                f"a été validée par l'administration IPM. Sa carte de prise en charge ({ayant_droit.numero_carte}) est désormais active."
            ),
            url_action=reverse("liste_ayants_droit"),
        )

    messages.success(request, f"L'ayant droit {ayant_droit.prenom} {ayant_droit.nom} a été validé avec succès.")
    return redirect(request.META.get("HTTP_REFERER") or "liste_patients")


@admin_required
@require_POST
def refuser_ayant_droit(request, pk):
    ayant_droit = get_object_or_404(
        Patient.objects.select_related("assure_principal__user"),
        pk=pk,
        type_beneficiaire=Patient.TypeBeneficiaire.AYANT_DROIT,
    )
    motif = (request.POST.get("motif_refus") or request.POST.get("motif") or "").strip() or "Pièce justificative non conforme ou informations incomplètes"
    ayant_droit.statut_validation = Patient.StatutValidation.REFUSE
    ayant_droit.date_decision = timezone.now()
    ayant_droit.valide_par = request.user
    ayant_droit.motif_refus = motif
    ayant_droit.save(update_fields=["statut_validation", "date_decision", "valide_par", "motif_refus"])

    journaliser(
        request,
        JournalActivite.Action.DECISION,
        str(ayant_droit),
        f"Refus de l'ayant droit {ayant_droit} : {motif}",
    )

    if ayant_droit.assure_principal and ayant_droit.assure_principal.user:
        emettre_notification(
            destinataire=ayant_droit.assure_principal.user,
            type_evenement=Notification.TypeEvenement.AYANT_DROIT_REFUSE,
            titre="Demande d'ayant droit refusée",
            message=(
                f"La demande de rattachement pour {ayant_droit.prenom} {ayant_droit.nom} "
                f"a été refusée par l'administration IPM. Motif : {motif}. "
                "Vous pouvez mettre à jour son dossier et joindre une pièce justificative conforme depuis votre espace."
            ),
            url_action=reverse("modifier_ayant_droit", args=[ayant_droit.pk]),
        )

    messages.warning(request, f"L'ayant droit {ayant_droit.prenom} {ayant_droit.nom} a été refusé.")
    return redirect(request.META.get("HTTP_REFERER") or "liste_patients")

