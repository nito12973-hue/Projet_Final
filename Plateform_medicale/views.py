import datetime
import unicodedata
from functools import wraps

import openpyxl
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    AyantDroitForm,
    ConsultationForm,
    EnvoyerNotificationForm,
    LoginForm,
    MedecinForm,
    MedecinProfilForm,
    OrdonnanceForm,
    PaiementReglementForm,
    PatientCreationForm,
    PatientForm,
    PharmacienAffectationForm,
    PlanCouvertureForm,
    PrestataireForm,
    PriseEnChargeForm,
    ProfilAssureForm,
    RendezVousAssureForm,
    RendezVousForm,
    ServiceMedicalForm,
    SetupWizardForm,
    UtilisateurCreationForm,
    UtilisateurModificationForm,
    generer_mot_de_passe,
    lier_fiche_medecin,
    lier_fiche_pharmacien,
)
from .models import (
    Consultation,
    Delivrance,
    Medecin,
    Notification,
    Ordonnance,
    Paiement,
    Patient,
    Pharmacien,
    PlanCouverture,
    Prestataire,
    PriseEnCharge,
    RendezVous,
    ServiceMedical,
    User,
    valider_telephone,
)


# ---------------------------------------------------------------------------
# Permissions par rôle
# ---------------------------------------------------------------------------

def role_required(*roles):
    """
    Restreint une vue aux rôles indiqués.

    Exemple :
        @role_required(User.Role.ADMIN, User.Role.MEDECIN)
        def ma_vue(request): ...
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def admin_required(view_func):
    """Restreint une vue au rôle ADMIN uniquement."""
    return role_required(User.Role.ADMIN)(view_func)


def user_role(request):
    """Context processor : expose le rôle et les notifications non lues de l'utilisateur connecté."""
    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        return {
            'current_role': user.role,
            'current_role_label': user.get_role_display(),
            'notifications_non_lues': user.notifications.filter(lue=False).count(),
        }
    return {'current_role': None, 'current_role_label': None, 'notifications_non_lues': 0}


# ---------------------------------------------------------------------------
# Authentification et tableaux de bord par rôle
# ---------------------------------------------------------------------------

def _admin_exists():
    return User.objects.filter(role=User.Role.ADMIN).exists()


def login_view(request):
    """Connexion par email et mot de passe. Le role est detecte en base."""
    if not _admin_exists():
        return redirect('setup_wizard')

    if request.user.is_authenticated:
        return redirect('post_login_redirect')

    form = LoginForm(request=request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.user)
        return redirect('post_login_redirect')

    return render(request, 'login.html', {'form': form})


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, 'Vous avez ete deconnecte.')
    return redirect('login')


@login_required
def post_login_redirect(request):
    """Redirection automatique vers le dashboard correspondant au role."""
    role = request.user.role
    if role == User.Role.ADMIN:
        return redirect('dashboard')
    if role == User.Role.ASSURE:
        return redirect('dashboard_assure')
    if role == User.Role.MEDECIN:
        return redirect('dashboard_medecin')
    if role == User.Role.PHARMACIEN:
        return redirect('dashboard_pharmacien')

    logout(request)
    messages.error(request, "Role inconnu. Contactez l'administration.")
    return redirect('login')


def setup_wizard(request):
    """
    Assistant de premiere installation.

    Accessible uniquement si aucun administrateur n'existe. Une fois le premier
    administrateur cree, l'assistant redirige toujours vers la connexion.
    """
    if _admin_exists():
        return redirect('login')

    form = SetupWizardForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(
            request,
            'Bienvenue ! Votre compte Super Administrateur a ete cree.',
        )
        return redirect('post_login_redirect')

    return render(request, 'setup_wizard.html', {'form': form})


@login_required
def changer_mot_de_passe(request):
    """
    Changement du mot de passe par l'utilisateur connecte (tous roles).

    Distinct de la reinitialisation par l'admin (Gestion des utilisateurs) :
    ici, l'utilisateur doit connaitre son mot de passe actuel.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, 'Mot de passe modifie avec succes.')
            return redirect('post_login_redirect')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'changer_mot_de_passe.html', {'form': form})


# ---------------------------------------------------------------------------
# Vitrine publique
# ---------------------------------------------------------------------------

def landing(request):
    """Page d'accueil publique de SantéSN (vitrine)."""
    return render(request, "landing.html")


# ---------------------------------------------------------------------------
# Dashboard administrateur
# ---------------------------------------------------------------------------

@admin_required
def dashboard(request):
    dernieres_prises_en_charge = PriseEnCharge.objects.select_related("patient").order_by("-date_demande")[:5]
    derniers_patients = Patient.objects.order_by("-id")[:5]
    contexte = {
        "total_patients": Patient.objects.count(),
        "total_medecins": Medecin.objects.count(),
        "total_prestataires": Prestataire.objects.count(),
        "total_services": ServiceMedical.objects.count(),
        "total_prises_en_charge": PriseEnCharge.objects.count(),
        "total_consultations": Consultation.objects.count(),
        "total_ordonnances": Ordonnance.objects.count(),
        "dernieres_prises_en_charge": dernieres_prises_en_charge,
        "derniers_patients": derniers_patients,
    }
    return render(request, "dashboard.html", contexte)


MOIS_ABREGES = ["Jan", "Fev", "Mar", "Avr", "Mai", "Jun", "Jul", "Aou", "Sep", "Oct", "Nov", "Dec"]


def _consultations_par_mois(nombre_mois=6):
    """Nombre de consultations par mois, sur les `nombre_mois` derniers mois (mois courant inclus)."""
    annee, mois = timezone.now().year, timezone.now().month
    mois_reference = []
    for _ in range(nombre_mois):
        mois_reference.append((annee, mois))
        mois -= 1
        if mois == 0:
            mois, annee = 12, annee - 1
    mois_reference.reverse()

    comptages = (
        Consultation.objects.annotate(mois=TruncMonth("date_consultation"))
        .values("mois")
        .annotate(total=Count("id"))
    )
    totaux_par_cle = {(c["mois"].year, c["mois"].month): c["total"] for c in comptages if c["mois"]}

    return {
        "labels": [f"{MOIS_ABREGES[m - 1]} {a}" for a, m in mois_reference],
        "totaux": [totaux_par_cle.get(cle, 0) for cle in mois_reference],
    }


def _donnees_rapports():
    """Comptages et agregats de synthese de l'activite de la plateforme (Phase 13)."""
    return {
        "utilisateurs_par_role": [
            {"label": label, "total": User.objects.filter(role=value).count()}
            for value, label in User.Role.choices
        ],
        "patients_par_type": [
            {"label": label, "total": Patient.objects.filter(type_beneficiaire=value).count()}
            for value, label in Patient.TypeBeneficiaire.choices
        ],
        "rendez_vous_par_statut": [
            {"label": label, "total": RendezVous.objects.filter(statut=value).count()}
            for value, label in RendezVous.Statut.choices
        ],
        "prises_en_charge_par_statut": [
            {"label": label, "total": PriseEnCharge.objects.filter(statut=value).count()}
            for value, label in PriseEnCharge.STATUT_CHOICES
        ],
        "total_consultations": Consultation.objects.count(),
        "total_ordonnances": Ordonnance.objects.count(),
        "total_delivrances": Delivrance.objects.count(),
        "total_prestataires_partenaires": Prestataire.objects.filter(partenaire=True).count(),
        "consultations_par_mois": _consultations_par_mois(),
    }


@admin_required
def rapports(request):
    """Synthese de l'activite de la plateforme : comptages et graphiques (Phase 13)."""
    return render(request, "rapports.html", _donnees_rapports())


@admin_required
def exporter_rapports_excel(request):
    donnees = _donnees_rapports()
    classeur = openpyxl.Workbook()
    classeur.remove(classeur.active)

    def ajouter_feuille(nom, entetes, lignes):
        feuille = classeur.create_sheet(nom)
        feuille.append(entetes)
        for ligne in lignes:
            feuille.append(ligne)
        for index, nom_colonne in enumerate(entetes, start=1):
            feuille.column_dimensions[get_column_letter(index)].width = max(len(str(nom_colonne)), 18)

    ajouter_feuille("Chiffres cles", ["Indicateur", "Total"], [
        ["Consultations", donnees["total_consultations"]],
        ["Ordonnances", donnees["total_ordonnances"]],
        ["Delivrances", donnees["total_delivrances"]],
        ["Prestataires partenaires", donnees["total_prestataires_partenaires"]],
    ])
    ajouter_feuille(
        "Utilisateurs par role", ["Role", "Total"],
        [[ligne["label"], ligne["total"]] for ligne in donnees["utilisateurs_par_role"]],
    )
    ajouter_feuille(
        "Assures par type", ["Type", "Total"],
        [[ligne["label"], ligne["total"]] for ligne in donnees["patients_par_type"]],
    )
    ajouter_feuille(
        "Rendez-vous par statut", ["Statut", "Total"],
        [[ligne["label"], ligne["total"]] for ligne in donnees["rendez_vous_par_statut"]],
    )
    ajouter_feuille(
        "Prises en charge par statut", ["Statut", "Total"],
        [[ligne["label"], ligne["total"]] for ligne in donnees["prises_en_charge_par_statut"]],
    )
    ajouter_feuille(
        "Consultations par mois", ["Mois", "Total"],
        list(zip(donnees["consultations_par_mois"]["labels"], donnees["consultations_par_mois"]["totaux"])),
    )

    reponse = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    reponse["Content-Disposition"] = 'attachment; filename="rapports_santesn.xlsx"'
    classeur.save(reponse)
    return reponse


@admin_required
def exporter_rapports_pdf(request):
    donnees = _donnees_rapports()
    reponse = HttpResponse(content_type="application/pdf")
    reponse["Content-Disposition"] = 'attachment; filename="rapports_santesn.pdf"'

    document = SimpleDocTemplate(reponse, pagesize=A4, title="Rapports SanteSN")
    styles = getSampleStyleSheet()
    elements = [Paragraph("Rapports SanteSN", styles["Title"]), Spacer(1, 12)]

    def ajouter_tableau(titre, entetes, lignes):
        elements.append(Paragraph(titre, styles["Heading2"]))
        tableau = Table([entetes] + lignes, hAlign="LEFT")
        tableau.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12885a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        elements.append(tableau)
        elements.append(Spacer(1, 16))

    ajouter_tableau("Chiffres cles", ["Indicateur", "Total"], [
        ["Consultations", str(donnees["total_consultations"])],
        ["Ordonnances", str(donnees["total_ordonnances"])],
        ["Delivrances", str(donnees["total_delivrances"])],
        ["Prestataires partenaires", str(donnees["total_prestataires_partenaires"])],
    ])
    ajouter_tableau(
        "Utilisateurs par role", ["Role", "Total"],
        [[ligne["label"], str(ligne["total"])] for ligne in donnees["utilisateurs_par_role"]],
    )
    ajouter_tableau(
        "Assures par type", ["Type", "Total"],
        [[ligne["label"], str(ligne["total"])] for ligne in donnees["patients_par_type"]],
    )
    ajouter_tableau(
        "Rendez-vous par statut", ["Statut", "Total"],
        [[ligne["label"], str(ligne["total"])] for ligne in donnees["rendez_vous_par_statut"]],
    )
    ajouter_tableau(
        "Prises en charge par statut", ["Statut", "Total"],
        [[ligne["label"], str(ligne["total"])] for ligne in donnees["prises_en_charge_par_statut"]],
    )
    ajouter_tableau(
        "Consultations par mois", ["Mois", "Total"],
        [
            [label, str(total)]
            for label, total in zip(
                donnees["consultations_par_mois"]["labels"], donnees["consultations_par_mois"]["totaux"]
            )
        ],
    )

    document.build(elements)
    return reponse


@admin_required
def liste_patients(request):
    patients = Patient.objects.select_related("assure_principal", "plan_couverture").all()

    type_beneficiaire = request.GET.get("type", "")
    if type_beneficiaire:
        patients = patients.filter(type_beneficiaire=type_beneficiaire)

    contexte = {
        "patients": patients,
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
            messages.success(request, "Assure ajoute.")
            return redirect("liste_patients")
    else:
        form = PatientCreationForm()
    return render(request, "ajouter_patient.html", {"form": form})


@admin_required
def liste_medecins(request):
    medecins = Medecin.objects.all()
    return render(request, "liste_medecins.html", {"medecins": medecins})


@admin_required
def ajouter_medecin(request):
    if request.method == "POST":
        form = MedecinForm(request.POST)
        if form.is_valid():
            medecin = form.save(commit=False)
            mot_de_passe = generer_mot_de_passe()
            utilisateur = User.objects.create_user(
                email=medecin.email,
                password=mot_de_passe,
                role=User.Role.MEDECIN,
                first_name=medecin.prenom,
                last_name=medecin.nom,
                phone_number=medecin.telephone,
            )
            medecin.user = utilisateur
            medecin.save()
            return render(
                request,
                "mot_de_passe_genere.html",
                {"utilisateur": utilisateur, "mot_de_passe": mot_de_passe, "action": "creation"},
            )
    else:
        form = MedecinForm()
    return render(request, "ajouter_medecin.html", {"form": form})


@admin_required
def liste_services(request):
    services = ServiceMedical.objects.all()
    return render(request, "liste_services.html", {"services": services})


@admin_required
def ajouter_service(request):
    if request.method == "POST":
        form = ServiceMedicalForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Service ajoute.")
            return redirect("liste_services")
    else:
        form = ServiceMedicalForm()
    return render(request, "ajouter_service.html", {"form": form})


@admin_required
def liste_prises_en_charge(request):
    prises_en_charge = PriseEnCharge.objects.select_related("patient").all()
    return render(
        request,
        "liste_prises_en_charge.html",
        {"prises_en_charge": prises_en_charge},
    )


@admin_required
def ajouter_prise_en_charge(request):
    """A la creation, le statut est toujours 'en_attente' : le champ n'est pas propose."""
    if request.method == "POST":
        form = PriseEnChargeForm(request.POST)
        form.fields.pop("statut")
        if form.is_valid():
            prise_en_charge = form.save(commit=False)
            prise_en_charge.statut = "en_attente"
            prise_en_charge.save()
            messages.success(request, "Prise en charge ajoutee.")
            return redirect("liste_prises_en_charge")
    else:
        form = PriseEnChargeForm()
        form.fields.pop("statut")
    return render(request, "ajouter_prise_en_charge.html", {"form": form})


@admin_required
def modifier_prise_en_charge(request, pk):
    prise_en_charge = get_object_or_404(PriseEnCharge, pk=pk)
    if request.method == "POST":
        form = PriseEnChargeForm(request.POST, instance=prise_en_charge)
        if form.is_valid():
            form.save()
            messages.success(request, "Prise en charge modifiee.")
            return redirect("liste_prises_en_charge")
    else:
        form = PriseEnChargeForm(instance=prise_en_charge)
    return render(
        request,
        "modifier_prise_en_charge.html",
        {"form": form, "prise_en_charge": prise_en_charge},
    )


@admin_required
def supprimer_prise_en_charge(request, pk):
    prise_en_charge = get_object_or_404(PriseEnCharge, pk=pk)
    if request.method == "POST":
        prise_en_charge.delete()
        messages.success(request, "Prise en charge supprimee.")
        return redirect("liste_prises_en_charge")
    return render(request, "confirmer_suppression.html", {"objet": prise_en_charge, "type": "Prise en charge"})


@admin_required
def liste_paiements(request):
    paiements = Paiement.objects.select_related(
        "consultation", "consultation__patient", "consultation__service"
    ).order_by("-consultation__date_consultation")

    statut = request.GET.get("statut", "")
    if statut:
        paiements = paiements.filter(statut=statut)

    contexte = {
        "paiements": paiements,
        "statut_choisi": statut,
        "statuts": Paiement.Statut.choices,
    }
    return render(request, "liste_paiements.html", contexte)


@admin_required
def marquer_paiement_regle(request, pk):
    paiement = get_object_or_404(Paiement, pk=pk)
    if paiement.statut == Paiement.Statut.REGLE:
        messages.info(request, "Ce paiement est deja regle.")
        return redirect("liste_paiements")

    if request.method == "POST":
        form = PaiementReglementForm(request.POST, instance=paiement)
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.statut = Paiement.Statut.REGLE
            paiement.date_reglement = timezone.now()
            paiement.save()
            messages.success(request, "Paiement marque comme regle.")
            return redirect("liste_paiements")
    else:
        form = PaiementReglementForm(instance=paiement)
    return render(request, "marquer_paiement_regle.html", {"form": form, "paiement": paiement})


@admin_required
def liste_prestataires(request):
    prestataires = Prestataire.objects.all()
    return render(request, "liste_prestataires.html", {"prestataires": prestataires})


@admin_required
def ajouter_prestataire(request):
    if request.method == "POST":
        form = PrestataireForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Prestataire ajoute.")
            return redirect("liste_prestataires")
    else:
        form = PrestataireForm()
    return render(request, "ajouter_prestataire.html", {"form": form})


@admin_required
def modifier_prestataire(request, pk):
    prestataire = get_object_or_404(Prestataire, pk=pk)
    if request.method == "POST":
        form = PrestataireForm(request.POST, instance=prestataire)
        if form.is_valid():
            form.save()
            messages.success(request, "Prestataire modifie.")
            return redirect("liste_prestataires")
    else:
        form = PrestataireForm(instance=prestataire)
    return render(request, "modifier_prestataire.html", {"form": form, "prestataire": prestataire})


@admin_required
def supprimer_prestataire(request, pk):
    prestataire = get_object_or_404(Prestataire, pk=pk)
    if request.method == "POST":
        prestataire.delete()
        messages.success(request, "Prestataire supprime.")
        return redirect("liste_prestataires")
    return render(request, "confirmer_suppression.html", {"objet": prestataire, "type": "Prestataire"})


@admin_required
def liste_plans_couverture(request):
    plans = PlanCouverture.objects.all()
    return render(request, "liste_plans_couverture.html", {"plans": plans})


@admin_required
def ajouter_plan_couverture(request):
    if request.method == "POST":
        form = PlanCouvertureForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Plan de couverture ajoute.")
            return redirect("liste_plans_couverture")
    else:
        form = PlanCouvertureForm()
    return render(request, "ajouter_plan_couverture.html", {"form": form})


@admin_required
def modifier_plan_couverture(request, pk):
    plan = get_object_or_404(PlanCouverture, pk=pk)
    if request.method == "POST":
        form = PlanCouvertureForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, "Plan de couverture modifie.")
            return redirect("liste_plans_couverture")
    else:
        form = PlanCouvertureForm(instance=plan)
    return render(request, "modifier_plan_couverture.html", {"form": form, "plan": plan})


@admin_required
def supprimer_plan_couverture(request, pk):
    plan = get_object_or_404(PlanCouverture, pk=pk)
    if request.method == "POST":
        plan.delete()
        messages.success(request, "Plan de couverture supprime.")
        return redirect("liste_plans_couverture")
    avertissement = _avertissement_cascade({"assure(s)/ayant(s) droit rattaches (plan retire, pas supprimes)": plan.beneficiaires.count()})
    return render(
        request,
        "confirmer_suppression.html",
        {"objet": plan, "type": "Plan de couverture", "avertissement": avertissement},
    )


# MODIFIER VUES
@admin_required
def modifier_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == "POST":
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, "Assure modifie.")
            return redirect("liste_patients")
    else:
        form = PatientForm(instance=patient)
    return render(request, "modifier_patient.html", {"form": form, "patient": patient})


@admin_required
def modifier_medecin(request, pk):
    medecin = get_object_or_404(Medecin, pk=pk)
    if request.method == "POST":
        form = MedecinForm(request.POST, instance=medecin)
        if form.is_valid():
            form.save()
            messages.success(request, "Medecin modifie.")
            return redirect("liste_medecins")
    else:
        form = MedecinForm(instance=medecin)
    return render(request, "modifier_medecin.html", {"form": form, "medecin": medecin})


@admin_required
def modifier_service(request, pk):
    service = get_object_or_404(ServiceMedical, pk=pk)
    if request.method == "POST":
        form = ServiceMedicalForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Service modifie.")
            return redirect("liste_services")
    else:
        form = ServiceMedicalForm(instance=service)
    return render(request, "modifier_service.html", {"form": form, "service": service})


def _avertissement_cascade(compteurs):
    """Construit un message d'avertissement a partir d'un dict {libelle: total}."""
    parties = [f"{total} {libelle}" for libelle, total in compteurs.items() if total]
    if not parties:
        return None
    return "Seront aussi supprimes : " + ", ".join(parties) + "."


# SUPPRIMER VUES
@admin_required
def supprimer_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == "POST":
        patient.delete()
        messages.success(request, "Assure supprime.")
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


@admin_required
def supprimer_medecin(request, pk):
    medecin = get_object_or_404(Medecin, pk=pk)
    if request.method == "POST":
        medecin.delete()
        messages.success(request, "Medecin supprime.")
        return redirect("liste_medecins")
    avertissement = _avertissement_cascade({
        "consultation(s)": medecin.consultation_set.count(),
        "rendez-vous": medecin.rendez_vous.count(),
    })
    return render(
        request,
        "confirmer_suppression.html",
        {"objet": medecin, "type": "Medecin", "avertissement": avertissement},
    )


@admin_required
def liste_pharmaciens(request):
    pharmaciens = Pharmacien.objects.select_related("user", "prestataire").all()
    return render(request, "liste_pharmaciens.html", {"pharmaciens": pharmaciens})


@admin_required
def modifier_pharmacien(request, pk):
    pharmacien = get_object_or_404(Pharmacien, pk=pk)
    if request.method == "POST":
        form = PharmacienAffectationForm(request.POST, instance=pharmacien)
        if form.is_valid():
            form.save()
            messages.success(request, "Pharmacien modifie.")
            return redirect("liste_pharmaciens")
    else:
        form = PharmacienAffectationForm(instance=pharmacien)
    return render(request, "modifier_pharmacien.html", {"form": form, "pharmacien": pharmacien})


@admin_required
def supprimer_service(request, pk):
    service = get_object_or_404(ServiceMedical, pk=pk)
    if request.method == "POST":
        service.delete()
        messages.success(request, "Service supprime.")
        return redirect("liste_services")
    return render(request, "confirmer_suppression.html", {"objet": service, "type": "Service"})


# ---------------------------------------------------------------------------
# Gestion des utilisateurs (Administrateur)
# ---------------------------------------------------------------------------

def _filtrer_utilisateurs(request):
    """Filtres partages entre la liste et l'export Excel des utilisateurs."""
    utilisateurs = User.objects.all()

    role = request.GET.get("role", "")
    statut = request.GET.get("statut", "")
    recherche = request.GET.get("q", "").strip()

    if role:
        utilisateurs = utilisateurs.filter(role=role)
    if statut == "actif":
        utilisateurs = utilisateurs.filter(is_active=True)
    elif statut == "inactif":
        utilisateurs = utilisateurs.filter(is_active=False)
    if recherche:
        utilisateurs = utilisateurs.filter(
            Q(email__icontains=recherche)
            | Q(first_name__icontains=recherche)
            | Q(last_name__icontains=recherche)
        )

    return utilisateurs, {"role": role, "statut": statut, "recherche": recherche}


@admin_required
def liste_utilisateurs(request):
    utilisateurs, filtres = _filtrer_utilisateurs(request)
    contexte = {
        "utilisateurs": utilisateurs,
        "roles": User.Role.choices,
        "role_selectionne": filtres["role"],
        "statut_selectionne": filtres["statut"],
        "recherche": filtres["recherche"],
    }
    return render(request, "liste_utilisateurs.html", contexte)


@admin_required
def exporter_utilisateurs_excel(request):
    utilisateurs, _ = _filtrer_utilisateurs(request)

    classeur = openpyxl.Workbook()
    feuille = classeur.active
    feuille.title = "Utilisateurs"
    entetes = ["Email", "Prenom", "Nom", "Telephone", "Role", "Statut", "Date de creation"]
    feuille.append(entetes)

    for utilisateur in utilisateurs:
        feuille.append([
            utilisateur.email,
            utilisateur.first_name,
            utilisateur.last_name,
            utilisateur.phone_number,
            utilisateur.get_role_display(),
            "Actif" if utilisateur.is_active else "Inactif",
            utilisateur.date_joined.strftime("%d/%m/%Y %H:%M"),
        ])

    for index, nom_colonne in enumerate(entetes, start=1):
        feuille.column_dimensions[get_column_letter(index)].width = max(len(nom_colonne), 18)

    reponse = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    reponse["Content-Disposition"] = 'attachment; filename="utilisateurs_santesn.xlsx"'
    classeur.save(reponse)
    return reponse


COLONNES_IMPORT_UTILISATEURS = [
    "Email", "Prenom", "Nom", "Telephone", "Role",
    "Date de naissance", "Specialite", "Prestataire", "Plan de couverture",
]


def _normaliser_texte_import(valeur):
    """Normalise une valeur de cellule pour une comparaison insensible aux accents/majuscules."""
    texte = "" if valeur is None else str(valeur).strip()
    texte = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode("ascii")
    return texte.upper()


_ROLES_PAR_LIBELLE_IMPORT = {}
for _valeur_role, _label_role in User.Role.choices:
    _ROLES_PAR_LIBELLE_IMPORT[_normaliser_texte_import(_valeur_role)] = _valeur_role
    _ROLES_PAR_LIBELLE_IMPORT[_normaliser_texte_import(_label_role)] = _valeur_role


def _analyser_ligne_import_utilisateurs(numero_ligne, valeurs):
    """
    Valide une ligne du fichier d'import (voir COLONNES_IMPORT_UTILISATEURS).

    Retourne (donnees, None) si la ligne est valide, ou (None, message_erreur)
    sinon. Ne touche jamais la base : l'import est valide en integralite
    avant toute creation (regle "tout ou rien").
    """
    valeurs = (tuple(valeurs) + (None,) * len(COLONNES_IMPORT_UTILISATEURS))[:len(COLONNES_IMPORT_UTILISATEURS)]
    email, prenom, nom, telephone, role_brut, date_naissance_brute, specialite, prestataire_brut, plan_brut = valeurs

    email = (email or "").strip()
    prenom = (prenom or "").strip()
    nom = (nom or "").strip()
    telephone = (telephone or "").strip() if telephone else ""

    if not email or not prenom or not nom:
        return None, f"Ligne {numero_ligne} : email, prenom et nom sont obligatoires."

    role = _ROLES_PAR_LIBELLE_IMPORT.get(_normaliser_texte_import(role_brut))
    if not role:
        return None, (
            f"Ligne {numero_ligne} : role '{role_brut}' inconnu "
            "(attendu : Administrateur, Assure, Medecin ou Pharmacien)."
        )

    if telephone:
        try:
            valider_telephone(telephone)
        except ValidationError:
            return None, f"Ligne {numero_ligne} : numero de telephone invalide."

    prestataire = None
    prestataire_nom = (prestataire_brut or "").strip() if prestataire_brut else ""
    if prestataire_nom:
        prestataire = Prestataire.objects.filter(nom__iexact=prestataire_nom).first()
        if not prestataire:
            return None, f"Ligne {numero_ligne} : prestataire '{prestataire_nom}' introuvable."

    plan_couverture = None
    plan_nom = (plan_brut or "").strip() if plan_brut else ""
    if plan_nom:
        plan_couverture = PlanCouverture.objects.filter(nom__iexact=plan_nom).first()
        if not plan_couverture:
            return None, f"Ligne {numero_ligne} : plan de couverture '{plan_nom}' introuvable."

    donnees = {
        "email": email,
        "prenom": prenom,
        "nom": nom,
        "telephone": telephone,
        "role": role,
        "prestataire": prestataire,
        "plan_couverture": plan_couverture,
    }

    if role == User.Role.MEDECIN:
        if not telephone:
            return None, f"Ligne {numero_ligne} : le telephone est obligatoire pour un medecin."
        specialite = (specialite or "").strip()
        if not specialite:
            return None, f"Ligne {numero_ligne} : la specialite est obligatoire pour un medecin."
        donnees["specialite"] = specialite
    elif role == User.Role.ASSURE:
        if not date_naissance_brute:
            return None, f"Ligne {numero_ligne} : la date de naissance est obligatoire pour un assure."
        if isinstance(date_naissance_brute, datetime.datetime):
            donnees["date_naissance"] = date_naissance_brute.date()
        elif isinstance(date_naissance_brute, datetime.date):
            donnees["date_naissance"] = date_naissance_brute
        else:
            try:
                donnees["date_naissance"] = datetime.datetime.strptime(
                    str(date_naissance_brute).strip(), "%d/%m/%Y"
                ).date()
            except ValueError:
                return None, (
                    f"Ligne {numero_ligne} : date de naissance invalide (format attendu JJ/MM/AAAA)."
                )

    return donnees, None


def _creer_comptes_import_utilisateurs(lignes_validees):
    """Cree en une transaction tous les comptes (et fiches metier) valides par l'import."""
    resultats = []
    with transaction.atomic():
        for donnees in lignes_validees:
            mot_de_passe = generer_mot_de_passe()
            utilisateur = User.objects.create_user(
                email=donnees["email"],
                password=mot_de_passe,
                role=donnees["role"],
                first_name=donnees["prenom"],
                last_name=donnees["nom"],
                phone_number=donnees["telephone"],
            )
            if donnees["role"] == User.Role.MEDECIN:
                Medecin.objects.create(
                    user=utilisateur,
                    nom=donnees["nom"],
                    prenom=donnees["prenom"],
                    specialite=donnees["specialite"],
                    telephone=donnees["telephone"],
                    email=donnees["email"],
                    prestataire=donnees["prestataire"],
                )
            elif donnees["role"] == User.Role.PHARMACIEN:
                Pharmacien.objects.create(user=utilisateur, prestataire=donnees["prestataire"])
            elif donnees["role"] == User.Role.ASSURE:
                Patient.objects.create(
                    user=utilisateur,
                    nom=donnees["nom"],
                    prenom=donnees["prenom"],
                    date_naissance=donnees["date_naissance"],
                    telephone=donnees["telephone"],
                    type_beneficiaire=Patient.TypeBeneficiaire.PRINCIPAL,
                    plan_couverture=donnees["plan_couverture"],
                )
            resultats.append({
                "email": utilisateur.email,
                "nom_complet": f"{utilisateur.first_name} {utilisateur.last_name}",
                "role": utilisateur.get_role_display(),
                "mot_de_passe": mot_de_passe,
            })
    return resultats


@admin_required
def importer_utilisateurs_excel(request):
    """
    Creation en masse de comptes (Assure principal / Medecin / Pharmacien /
    Administrateur) depuis un fichier Excel : voir COLONNES_IMPORT_UTILISATEURS.

    Regle "tout ou rien" : la moindre ligne invalide bloque tout l'import
    (aucun compte cree), pour eviter un import partiel difficile a auditer.
    """
    erreurs = []
    if request.method == "POST":
        fichier = request.FILES.get("fichier")
        if not fichier:
            erreurs.append("Choisissez un fichier Excel (.xlsx) a importer.")
        else:
            try:
                classeur = openpyxl.load_workbook(fichier, data_only=True)
            except Exception:
                erreurs.append(
                    "Fichier illisible : verifiez qu'il s'agit bien d'un fichier Excel (.xlsx) valide."
                )
            else:
                feuille = classeur.active
                entetes = next(feuille.iter_rows(min_row=1, max_row=1, values_only=True), ())
                entetes_normalisees = [_normaliser_texte_import(entete) for entete in entetes]
                entetes_attendues = [_normaliser_texte_import(colonne) for colonne in COLONNES_IMPORT_UTILISATEURS]

                if entetes_normalisees[:len(entetes_attendues)] != entetes_attendues:
                    erreurs.append(
                        "En-tetes de colonnes invalides : utilisez le modele telechargeable ci-dessous."
                    )
                else:
                    lignes_brutes = [
                        (numero, valeurs)
                        for numero, valeurs in enumerate(
                            feuille.iter_rows(min_row=2, values_only=True), start=2
                        )
                        if valeurs and not all(valeur in (None, "") for valeur in valeurs)
                    ]
                    if not lignes_brutes:
                        erreurs.append("Le fichier ne contient aucune ligne a importer.")
                    else:
                        donnees_valides = []
                        emails_vus = set()
                        for numero_ligne, valeurs in lignes_brutes:
                            donnees, erreur = _analyser_ligne_import_utilisateurs(numero_ligne, valeurs)
                            if erreur:
                                erreurs.append(erreur)
                                continue
                            email_normalise = donnees["email"].lower()
                            if email_normalise in emails_vus:
                                erreurs.append(
                                    f"Ligne {numero_ligne} : email '{donnees['email']}' en double dans le fichier."
                                )
                                continue
                            if User.objects.filter(email__iexact=donnees["email"]).exists():
                                erreurs.append(
                                    f"Ligne {numero_ligne} : email '{donnees['email']}' "
                                    "deja utilise par un compte existant."
                                )
                                continue
                            emails_vus.add(email_normalise)
                            donnees_valides.append(donnees)

                        if not erreurs:
                            resultats = _creer_comptes_import_utilisateurs(donnees_valides)
                            return render(
                                request, "resultat_import_utilisateurs.html", {"resultats": resultats}
                            )

    return render(request, "importer_utilisateurs.html", {"erreurs": erreurs})


@admin_required
def telecharger_modele_import_utilisateurs(request):
    classeur = openpyxl.Workbook()
    feuille = classeur.active
    feuille.title = "Import utilisateurs"
    feuille.append(COLONNES_IMPORT_UTILISATEURS)
    feuille.append([
        "awa.diop@exemple.sn", "Awa", "Diop", "770000000", "Assure",
        "15/03/1990", "", "", "",
    ])
    feuille.append([
        "moussa.fall@exemple.sn", "Moussa", "Fall", "770000001", "Medecin",
        "", "Medecine generale", "", "",
    ])

    for index, nom_colonne in enumerate(COLONNES_IMPORT_UTILISATEURS, start=1):
        feuille.column_dimensions[get_column_letter(index)].width = max(len(nom_colonne), 20)

    reponse = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    reponse["Content-Disposition"] = 'attachment; filename="modele_import_utilisateurs.xlsx"'
    classeur.save(reponse)
    return reponse


@admin_required
def ajouter_utilisateur(request):
    if request.method == "POST":
        form = UtilisateurCreationForm(request.POST)
        if form.is_valid():
            utilisateur = form.save()
            return render(
                request,
                "mot_de_passe_genere.html",
                {
                    "utilisateur": utilisateur,
                    "mot_de_passe": form.mot_de_passe_genere,
                    "action": "creation",
                },
            )
    else:
        form = UtilisateurCreationForm()
    return render(request, "ajouter_utilisateur.html", {"form": form})


@admin_required
def modifier_utilisateur(request, pk):
    utilisateur = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UtilisateurModificationForm(request.POST, instance=utilisateur)
        if form.is_valid():
            nouveau_role = form.cleaned_data["role"]
            if utilisateur.pk == request.user.pk and nouveau_role != request.user.role:
                form.add_error("role", "Vous ne pouvez pas modifier votre propre role.")
            else:
                utilisateur_modifie = form.save()
                lier_fiche_medecin(utilisateur_modifie)
                lier_fiche_pharmacien(utilisateur_modifie)
                messages.success(request, "Utilisateur modifie avec succes.")
                return redirect("liste_utilisateurs")
    else:
        form = UtilisateurModificationForm(instance=utilisateur)
    return render(
        request,
        "modifier_utilisateur.html",
        {"form": form, "utilisateur": utilisateur},
    )


@admin_required
@require_POST
def activer_desactiver_utilisateur(request, pk):
    utilisateur = get_object_or_404(User, pk=pk)
    if utilisateur.pk == request.user.pk:
        messages.error(request, "Vous ne pouvez pas desactiver votre propre compte.")
        return redirect("liste_utilisateurs")

    utilisateur.is_active = not utilisateur.is_active
    utilisateur.save(update_fields=["is_active"])
    if utilisateur.is_active:
        messages.success(request, f"Compte de {utilisateur} active.")
    else:
        messages.success(request, f"Compte de {utilisateur} desactive.")
    return redirect("liste_utilisateurs")


@admin_required
def reinitialiser_mot_de_passe(request, pk):
    utilisateur = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        nouveau_mot_de_passe = generer_mot_de_passe()
        utilisateur.set_password(nouveau_mot_de_passe)
        utilisateur.save(update_fields=["password"])
        return render(
            request,
            "mot_de_passe_genere.html",
            {
                "utilisateur": utilisateur,
                "mot_de_passe": nouveau_mot_de_passe,
                "action": "reinitialisation",
            },
        )
    return render(request, "reinitialiser_mot_de_passe.html", {"utilisateur": utilisateur})


@admin_required
def supprimer_utilisateur(request, pk):
    utilisateur = get_object_or_404(User, pk=pk)
    if utilisateur.pk == request.user.pk:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect("liste_utilisateurs")

    if request.method == "POST":
        utilisateur.delete()
        messages.success(request, "Utilisateur supprime.")
        return redirect("liste_utilisateurs")
    return render(
        request,
        "confirmer_suppression.html",
        {"objet": utilisateur, "type": "Utilisateur"},
    )


# ---------------------------------------------------------------------------
# Espace Medecin
# ---------------------------------------------------------------------------

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
    rendez_vous_a_venir = RendezVous.objects.filter(
        medecin=medecin, date_heure__gte=maintenant
    ).exclude(statut=RendezVous.Statut.ANNULE)

    contexte = {
        "total_patients": _patients_du_medecin(medecin).count(),
        "total_rendez_vous_a_venir": rendez_vous_a_venir.count(),
        "total_consultations": Consultation.objects.filter(medecin=medecin).count(),
        "total_ordonnances": Ordonnance.objects.filter(consultation__medecin=medecin).count(),
        "prochains_rendez_vous": rendez_vous_a_venir.select_related("patient").order_by("date_heure")[:5],
        "medecin": medecin,
    }
    return render(request, "dashboard_medecin.html", contexte)


@role_required(User.Role.MEDECIN)
def agenda_medecin(request):
    medecin = _medecin_courant(request)
    if medecin is None:
        return render(request, "medecin_fiche_manquante.html")

    rendez_vous = RendezVous.objects.filter(medecin=medecin).select_related("patient", "prestataire")
    return render(request, "agenda_medecin.html", {"rendez_vous": rendez_vous})


@role_required(User.Role.MEDECIN)
def ajouter_rendez_vous(request):
    medecin = _medecin_courant(request)
    if medecin is None:
        return render(request, "medecin_fiche_manquante.html")

    if request.method == "POST":
        form = RendezVousForm(request.POST)
        if form.is_valid():
            rendez_vous = form.save(commit=False)
            rendez_vous.medecin = medecin
            rendez_vous.save()
            messages.success(request, "Rendez-vous cree.")
            return redirect("agenda_medecin")
    else:
        form = RendezVousForm()
    return render(request, "ajouter_rendez_vous.html", {"form": form})


@role_required(User.Role.MEDECIN)
@require_POST
def changer_statut_rendez_vous(request, pk):
    medecin = _medecin_courant(request)
    rendez_vous = get_object_or_404(RendezVous, pk=pk, medecin=medecin)
    nouveau_statut = request.POST.get("statut")
    if nouveau_statut in RendezVous.Statut.values:
        rendez_vous.statut = nouveau_statut
        rendez_vous.save(update_fields=["statut"])
        messages.success(request, "Statut du rendez-vous mis a jour.")
    return redirect("agenda_medecin")


@role_required(User.Role.MEDECIN)
def mes_patients(request):
    medecin = _medecin_courant(request)
    if medecin is None:
        return render(request, "medecin_fiche_manquante.html")
    return render(request, "mes_patients.html", {"patients": _patients_du_medecin(medecin)})


@role_required(User.Role.MEDECIN)
def historique_consultations(request):
    medecin = _medecin_courant(request)
    if medecin is None:
        return render(request, "medecin_fiche_manquante.html")

    consultations = Consultation.objects.filter(medecin=medecin).select_related(
        "patient", "service", "prise_en_charge"
    ).prefetch_related("ordonnance_set").order_by("-date_consultation")
    return render(request, "historique_consultations.html", {"consultations": consultations})


@role_required(User.Role.MEDECIN)
def ajouter_consultation_medecin(request):
    medecin = _medecin_courant(request)
    if medecin is None:
        return render(request, "medecin_fiche_manquante.html")

    if request.method == "POST":
        form = ConsultationForm(request.POST)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.medecin = medecin
            consultation.save()
            Paiement.calculer_pour(consultation).save()
            messages.success(request, "Consultation enregistree.")
            return redirect("ajouter_ordonnance_medecin", consultation_pk=consultation.pk)
    else:
        form = ConsultationForm()
    return render(request, "ajouter_consultation_medecin.html", {"form": form})


@role_required(User.Role.MEDECIN)
def ajouter_ordonnance_medecin(request, consultation_pk):
    medecin = _medecin_courant(request)
    consultation = get_object_or_404(Consultation, pk=consultation_pk, medecin=medecin)

    if request.method == "POST":
        form = OrdonnanceForm(request.POST)
        if form.is_valid():
            ordonnance = form.save(commit=False)
            ordonnance.consultation = consultation
            ordonnance.save()
            return redirect("voir_ordonnance_medecin", pk=ordonnance.pk)
    else:
        form = OrdonnanceForm()
    return render(
        request,
        "ajouter_ordonnance_medecin.html",
        {"form": form, "consultation": consultation},
    )


@role_required(User.Role.MEDECIN)
def voir_ordonnance_medecin(request, pk):
    medecin = _medecin_courant(request)
    ordonnance = get_object_or_404(Ordonnance, pk=pk, consultation__medecin=medecin)
    return render(
        request,
        "voir_ordonnance.html",
        {"ordonnance": ordonnance, "retour_url": "historique_consultations"},
    )


@role_required(User.Role.MEDECIN)
def modifier_profil_medecin(request):
    medecin = _medecin_courant(request)
    if medecin is None:
        return render(request, "medecin_fiche_manquante.html")

    if request.method == "POST":
        form = MedecinProfilForm(request.POST, instance=medecin)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis a jour.")
            return redirect("modifier_profil_medecin")
    else:
        form = MedecinProfilForm(instance=medecin)
    return render(request, "modifier_profil_medecin.html", {"form": form, "medecin": medecin})


# ---------------------------------------------------------------------------
# Espace Pharmacien
# ---------------------------------------------------------------------------

def _pharmacien_courant(request):
    return getattr(request.user, "pharmacien", None)


@role_required(User.Role.PHARMACIEN)
def dashboard_pharmacien(request):
    pharmacien = _pharmacien_courant(request)
    if pharmacien is None:
        return render(request, "pharmacien_fiche_manquante.html")

    delivrances = Delivrance.objects.filter(pharmacien=pharmacien)
    contexte = {
        "total_delivrances": delivrances.count(),
        "dernieres_delivrances": delivrances.select_related(
            "ordonnance__consultation__patient"
        ).order_by("-date_delivrance")[:5],
        "pharmacien": pharmacien,
    }
    return render(request, "dashboard_pharmacien.html", contexte)


@role_required(User.Role.PHARMACIEN)
def scanner_ordonnance(request):
    pharmacien = _pharmacien_courant(request)
    if pharmacien is None:
        return render(request, "pharmacien_fiche_manquante.html")

    ordonnance = None
    if request.method == "POST":
        code = request.POST.get("code_qr", "").strip().upper()
        try:
            ordonnance = Ordonnance.objects.select_related(
                "consultation__patient", "consultation__medecin"
            ).get(code_qr=code)
        except Ordonnance.DoesNotExist:
            messages.error(request, "Aucune ordonnance ne correspond a ce code.")

    return render(request, "scanner_ordonnance.html", {"ordonnance": ordonnance})


@role_required(User.Role.PHARMACIEN)
@require_POST
def valider_delivrance(request, pk):
    pharmacien = _pharmacien_courant(request)
    ordonnance = get_object_or_404(Ordonnance, pk=pk)
    if hasattr(ordonnance, "delivrance"):
        messages.error(request, "Cette ordonnance a deja ete delivree.")
    else:
        Delivrance.objects.create(ordonnance=ordonnance, pharmacien=pharmacien)
        messages.success(request, "Delivrance validee.")
    return redirect("historique_delivrances")


@role_required(User.Role.PHARMACIEN)
def historique_delivrances(request):
    pharmacien = _pharmacien_courant(request)
    if pharmacien is None:
        return render(request, "pharmacien_fiche_manquante.html")

    delivrances = Delivrance.objects.filter(pharmacien=pharmacien).select_related(
        "ordonnance__consultation__patient", "ordonnance__consultation__medecin"
    ).order_by("-date_delivrance")
    return render(request, "historique_delivrances.html", {"delivrances": delivrances})


# ---------------------------------------------------------------------------
# Espace Assure
# ---------------------------------------------------------------------------

def _patient_principal(request):
    return getattr(request.user, "patient", None)


def _beneficiaires(patient):
    return Patient.objects.filter(
        Q(pk=patient.pk) | Q(assure_principal=patient)
    ).order_by("nom", "prenom")


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

    contexte = {
        "patient": patient,
        "total_ayants_droit": beneficiaires.exclude(pk=patient.pk).count(),
        "total_rendez_vous_a_venir": rendez_vous_a_venir.count(),
        "total_ordonnances": Ordonnance.objects.filter(consultation__patient__in=beneficiaires).count(),
        "prochains_rendez_vous": rendez_vous_a_venir.select_related(
            "medecin", "prestataire", "patient"
        ).order_by("date_heure")[:5],
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
            messages.success(request, "Profil enregistre.")
            return redirect("dashboard_assure")
    else:
        initial = {}
        if patient is None:
            initial = {"nom": request.user.last_name, "prenom": request.user.first_name}
        form = ProfilAssureForm(instance=patient, initial=initial)

    return render(request, "mon_profil_assure.html", {"form": form, "patient": patient})


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
            messages.success(request, "Ayant droit ajoute.")
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
            messages.success(request, "Ayant droit modifie.")
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
        ayant_droit.delete()
        messages.success(request, "Ayant droit supprime.")
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
    rendez_vous = RendezVous.objects.filter(patient__in=beneficiaires).select_related(
        "patient", "medecin", "prestataire"
    )
    return render(request, "mes_rendez_vous.html", {"rendez_vous": rendez_vous})


@role_required(User.Role.ASSURE)
def ajouter_rendez_vous_assure(request):
    patient = _patient_principal(request)
    if patient is None:
        return redirect("mon_profil_assure")
    beneficiaires = _beneficiaires(patient)

    if request.method == "POST":
        form = RendezVousAssureForm(request.POST, beneficiaires=beneficiaires)
        if form.is_valid():
            form.save()
            messages.success(request, "Demande de rendez-vous envoyee.")
            return redirect("mes_rendez_vous_assure")
    else:
        form = RendezVousAssureForm(beneficiaires=beneficiaires)
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
        messages.success(request, "Rendez-vous annule.")
    else:
        messages.error(request, "Ce rendez-vous ne peut plus etre annule.")
    return redirect("mes_rendez_vous_assure")


@role_required(User.Role.ASSURE)
def mes_ordonnances_assure(request):
    patient = _patient_principal(request)
    if patient is None:
        return redirect("mon_profil_assure")
    beneficiaires = _beneficiaires(patient)
    ordonnances = Ordonnance.objects.filter(
        consultation__patient__in=beneficiaires
    ).select_related("consultation__patient", "consultation__medecin").order_by("-date_creation")
    return render(request, "mes_ordonnances.html", {"ordonnances": ordonnances})


@role_required(User.Role.ASSURE)
def voir_ordonnance_assure(request, pk):
    patient = _patient_principal(request)
    beneficiaires = _beneficiaires(patient) if patient else Patient.objects.none()
    ordonnance = get_object_or_404(Ordonnance, pk=pk, consultation__patient__in=beneficiaires)
    return render(
        request,
        "voir_ordonnance.html",
        {"ordonnance": ordonnance, "retour_url": "mes_ordonnances_assure"},
    )


@role_required(User.Role.ASSURE)
def mon_historique_assure(request):
    patient = _patient_principal(request)
    if patient is None:
        return redirect("mon_profil_assure")
    beneficiaires = _beneficiaires(patient)
    consultations = Consultation.objects.filter(patient__in=beneficiaires).select_related(
        "patient", "medecin", "service", "paiement"
    ).order_by("-date_consultation")
    return render(request, "mon_historique.html", {"consultations": consultations})


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

@admin_required
def envoyer_notification(request):
    if request.method == "POST":
        form = EnvoyerNotificationForm(request.POST)
        if form.is_valid():
            message = form.cleaned_data["message"]
            destinataire = form.cleaned_data["destinataire"]
            role = form.cleaned_data["role"]

            if destinataire:
                destinataires = [destinataire]
            else:
                destinataires = list(User.objects.filter(role=role, is_active=True))

            Notification.objects.bulk_create(
                [Notification(destinataire=u, message=message) for u in destinataires]
            )
            messages.success(request, f"Notification envoyee a {len(destinataires)} utilisateur(s).")
            return redirect("liste_notifications_envoyees")
    else:
        form = EnvoyerNotificationForm()
    return render(request, "envoyer_notification.html", {"form": form})


@admin_required
def liste_notifications_envoyees(request):
    notifications = Notification.objects.select_related("destinataire").all()[:200]
    return render(request, "liste_notifications_envoyees.html", {"notifications": notifications})


@login_required
def mes_notifications(request):
    notifications = request.user.notifications.all()
    return render(request, "mes_notifications.html", {"notifications": notifications})


@login_required
@require_POST
def marquer_notification_lue(request, pk):
    notification = get_object_or_404(Notification, pk=pk, destinataire=request.user)
    notification.lue = True
    notification.save(update_fields=["lue"])
    return redirect("mes_notifications")
