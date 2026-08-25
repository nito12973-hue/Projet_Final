"""CRUD Patients (liste, ajout, modification, suppression) + carte de prise en charge."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from ..forms import PatientCreationForm, PatientForm, generer_mot_de_passe
from ..models import JournalActivite, Patient, User
from .utils import _avertissement_cascade, _paginer, _trier, admin_required, journaliser
from .medecin_espace import _medecin_courant


@admin_required
def liste_patients(request):
    patients = Patient.objects.select_related("assure_principal", "plan_couverture").all()

    type_beneficiaire = request.GET.get("type", "")
    if type_beneficiaire:
        patients = patients.filter(type_beneficiaire=type_beneficiaire)

    patients = _trier(
        request, patients,
        ["id", "nom", "type_beneficiaire", "assure_principal__nom", "numero_carte", "plan_couverture__nom"],
        ["nom", "prenom"],
    )

    contexte = {
        "patients": _paginer(request, patients),
        "types_beneficiaire": Patient.TypeBeneficiaire.choices,
        "type_selectionne": type_beneficiaire,
    }
    return render(request, "liste_patients.html", contexte)


@admin_required
def ajouter_patient(request):
    if request.method == "POST":
        form = PatientCreationForm(request.POST)
        if form.is_valid():
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
                return render(
                    request,
                    "mot_de_passe_genere.html",
                    {"utilisateur": utilisateur, "mot_de_passe": mot_de_passe, "action": "creation"},
                )
            patient.save()
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
    if request.method == "POST":
        # Le User (assure principal uniquement, jamais un ayant droit) doit
        # etre desactive : sinon la fiche disparait mais le compte de
        # connexion reste actif, et mon_profil_assure se recree tout seul
        # une fiche Patient a la prochaine connexion.
        if patient.user:
            patient.user.is_active = False
            patient.user.save(update_fields=["is_active"])
        journaliser(
            request, JournalActivite.Action.SUPPRESSION, f"Assuré : {patient}",
            "compte de connexion désactivé" if patient.user else "sans compte de connexion",
        )
        patient.delete()
        messages.success(request, "Assuré supprimé.")
        return redirect("liste_patients")
    avertissement = _avertissement_cascade({
        "ayant(s) droit": patient.ayants_droit.count(),
        "consultation(s)": patient.consultation_set.count(),
        "prise(s) en charge": patient.priseencharge_set.count(),
        "rendez-vous": patient.rendez_vous.count(),
    })
    return render(
        request,
        "confirmer_suppression.html",
        {"objet": patient, "type": "Patient", "avertissement": avertissement},
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
    })
