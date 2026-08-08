import secrets
import string

from django import forms
from django.contrib.auth import authenticate, password_validation
from django.core.cache import cache
from django.utils import timezone

from .models import (
    Consultation,
    Medecin,
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
)

MAX_TENTATIVES_CONNEXION = 5
DUREE_BLOCAGE_SECONDES = 5 * 60


def generer_mot_de_passe():
    """Genere un mot de passe temporaire aleatoire (creation ou reinitialisation)."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(12))


def lier_fiche_medecin(utilisateur):
    """
    Cree la fiche metier Medecin liee a un compte de role MEDECIN, si elle
    n'existe pas encore. Sans cette fiche, le compte n'a aucun tableau de
    bord Medecin fonctionnel (pas de patients, agenda, consultations).
    """
    if utilisateur.role != User.Role.MEDECIN or hasattr(utilisateur, 'medecin'):
        return
    Medecin.objects.create(
        user=utilisateur,
        nom=utilisateur.last_name,
        prenom=utilisateur.first_name,
        specialite='',
        telephone=utilisateur.phone_number,
        email=utilisateur.email,
    )


def lier_fiche_pharmacien(utilisateur):
    """
    Cree la fiche metier Pharmacien liee a un compte de role PHARMACIEN, si
    elle n'existe pas encore. Sans cette fiche, le compte n'a aucun tableau
    de bord Pharmacien fonctionnel.
    """
    if utilisateur.role != User.Role.PHARMACIEN or hasattr(utilisateur, 'pharmacien'):
        return
    Pharmacien.objects.create(user=utilisateur)


class LoginForm(forms.Form):
    """Connexion : email + mot de passe uniquement. Aucun choix de rôle."""

    email = forms.EmailField(
        label='Adresse email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'vous@exemple.sn',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre mot de passe',
        }),
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            cle_cache = f'tentatives_connexion:{email.lower()}'
            tentatives = cache.get(cle_cache, 0)
            if tentatives >= MAX_TENTATIVES_CONNEXION:
                raise forms.ValidationError(
                    'Trop de tentatives de connexion. Réessayez dans quelques minutes.'
                )

            self.user = authenticate(self.request, username=email, password=password)
            if self.user is None:
                cache.set(cle_cache, tentatives + 1, DUREE_BLOCAGE_SECONDES)
                raise forms.ValidationError(
                    'Email ou mot de passe incorrect.'
                )
            if not self.user.is_active:
                raise forms.ValidationError(
                    "Ce compte est désactivé. Contactez l'administration."
                )
            cache.delete(cle_cache)
        return cleaned_data


class SetupWizardForm(forms.ModelForm):
    """Création du premier Super Administrateur (assistant d'installation)."""

    password1 = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Au moins 8 caractères, pas uniquement des chiffres.',
    )
    password2 = forms.CharField(
        label='Confirmation du mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Les deux mots de passe ne correspondent pas.')
        password_validation.validate_password(password2)
        return password2

    def save(self, commit=True):
        return User.objects.create_superuser(
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            phone_number=self.cleaned_data['phone_number'],
        )


class UtilisateurCreationForm(forms.ModelForm):
    """Creation d'un compte par l'administrateur : le mot de passe est genere automatiquement."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Un seul administrateur, jamais recreable depuis l'interface classique
        # (voir UtilisateurModificationForm) : cette vue n'est accessible qu'a
        # un administrateur deja existant (@admin_required), donc ADMIN n'est
        # jamais un choix valide ici.
        self.fields['role'].choices = [
            choix for choix in User.Role.choices if choix[0] != User.Role.ADMIN
        ]

    def save(self, commit=True):
        self.mot_de_passe_genere = generer_mot_de_passe()
        utilisateur = super().save(commit=False)
        utilisateur.set_password(self.mot_de_passe_genere)
        if commit:
            utilisateur.save()
            lier_fiche_medecin(utilisateur)
            lier_fiche_pharmacien(utilisateur)
        return utilisateur


class UtilisateurModificationForm(forms.ModelForm):
    """Modification du profil et du role d'un utilisateur existant (par l'administrateur)."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Un seul administrateur, comme dans un veritable SaaS : personne ne
        # peut etre promu ADMIN depuis cette interface. Exception : editer la
        # fiche de l'administrateur actuel doit continuer a afficher/accepter
        # son propre role (ADMIN), sinon le formulaire casse pour lui -- le
        # garde-fou qui l'empeche de changer SON role reste dans la vue
        # modifier_utilisateur (deja en place, non modifie ici).
        if self.instance.role != User.Role.ADMIN:
            self.fields['role'].choices = [
                choix for choix in User.Role.choices if choix[0] != User.Role.ADMIN
            ]


class RendezVousForm(forms.ModelForm):
    """
    Creation d'un rendez-vous par le medecin.

    Le champ patient n'est volontairement pas restreint aux patients deja
    suivis par ce medecin : un nouveau patient peut le consulter pour la
    premiere fois (comme dans un annuaire de soins partage).
    """

    date_heure = forms.DateTimeField(
        label='Date et heure',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        input_formats=['%Y-%m-%dT%H:%M'],
    )
    prestataire = forms.ModelChoiceField(
        queryset=Prestataire.objects.filter(partenaire=True),
        required=False,
        label='Prestataire',
    )

    class Meta:
        model = RendezVous
        fields = ['patient', 'prestataire', 'date_heure', 'motif']

    def clean_date_heure(self):
        date_heure = self.cleaned_data['date_heure']
        if date_heure < timezone.now():
            raise forms.ValidationError("La date et l'heure du rendez-vous ne peuvent pas être dans le passé.")
        return date_heure


class ConsultationForm(forms.ModelForm):
    """Creation d'une consultation par le medecin connecte."""

    date_consultation = forms.DateTimeField(
        label='Date de consultation',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        input_formats=['%Y-%m-%dT%H:%M'],
    )

    class Meta:
        model = Consultation
        fields = ['patient', 'service', 'prise_en_charge', 'date_consultation', 'diagnostic', 'traitement']

    def clean(self):
        cleaned_data = super().clean()
        patient = cleaned_data.get('patient')
        prise_en_charge = cleaned_data.get('prise_en_charge')
        if patient and prise_en_charge and prise_en_charge.patient_id != patient.pk:
            self.add_error(
                'prise_en_charge',
                "Cette prise en charge ne correspond pas au patient sélectionné.",
            )
        return cleaned_data


class OrdonnanceForm(forms.ModelForm):
    """Creation d'une ordonnance rattachee a une consultation (le QR est genere automatiquement)."""

    class Meta:
        model = Ordonnance
        fields = ['medicaments']
        widgets = {
            'medicaments': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': 'Un medicament par ligne : nom, dosage, posologie...',
            }),
        }


class MedecinProfilForm(forms.ModelForm):
    """Le medecin ne modifie que ses informations professionnelles (pas email/role, geres par l'admin)."""

    class Meta:
        model = Medecin
        fields = ['specialite', 'telephone']


class ProfilAssureForm(forms.ModelForm):
    """
    Completion/modification du profil assure principal.

    Utilise a la fois pour la premiere completion (instance=None, aucune fiche
    Patient liee) et pour les modifications ulterieures (instance existante).
    """

    class Meta:
        model = Patient
        fields = ['nom', 'prenom', 'date_naissance', 'telephone', 'adresse']
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date'}),
        }


class AyantDroitForm(forms.ModelForm):
    """Creation/modification d'un ayant droit par l'assure principal."""

    class Meta:
        model = Patient
        fields = ['nom', 'prenom', 'date_naissance', 'telephone', 'lien_parente']
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date'}),
        }


class RendezVousAssureForm(forms.ModelForm):
    """Demande de rendez-vous par l'assure, pour lui-meme ou un ayant droit."""

    medecin = forms.ModelChoiceField(queryset=Medecin.objects.all(), label='Médecin')
    prestataire = forms.ModelChoiceField(
        queryset=Prestataire.objects.filter(partenaire=True),
        required=False,
        label='Prestataire',
    )
    date_heure = forms.DateTimeField(
        label='Date et heure souhaitées',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        input_formats=['%Y-%m-%dT%H:%M'],
    )

    class Meta:
        model = RendezVous
        fields = ['patient', 'medecin', 'prestataire', 'date_heure', 'motif']
        labels = {'patient': 'Beneficiaire'}

    def __init__(self, *args, beneficiaires=None, **kwargs):
        super().__init__(*args, **kwargs)
        if beneficiaires is not None:
            self.fields['patient'].queryset = beneficiaires

    def clean_date_heure(self):
        date_heure = self.cleaned_data['date_heure']
        if date_heure < timezone.now():
            raise forms.ValidationError("La date et l'heure du rendez-vous ne peuvent pas être dans le passé.")
        return date_heure


class PrestataireForm(forms.ModelForm):
    """Creation/modification d'un prestataire de sante partenaire (par l'administrateur)."""

    class Meta:
        model = Prestataire
        fields = [
            'nom', 'type_prestataire', 'adresse', 'ville', 'telephone',
            'partenaire', 'date_conventionnement', 'latitude', 'longitude',
        ]
        widgets = {
            'adresse': forms.Textarea(attrs={'rows': 3}),
            'date_conventionnement': forms.DateInput(attrs={'type': 'date'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }


class PharmacienAffectationForm(forms.ModelForm):
    """L'administrateur affecte un pharmacien a un prestataire (pharmacie partenaire)."""

    prestataire = forms.ModelChoiceField(
        queryset=Prestataire.objects.filter(type_prestataire=Prestataire.Type.PHARMACIE),
        required=False,
        label='Pharmacie',
    )

    class Meta:
        model = Pharmacien
        fields = ['prestataire']


class PatientForm(forms.ModelForm):
    """
    Creation/modification complete d'un assure ou d'un ayant droit par
    l'administrateur, y compris l'attribution du plan de couverture
    (responsabilite RH/assurance, pas celle de l'assure lui-meme).
    """

    class Meta:
        model = Patient
        fields = [
            'nom', 'prenom', 'date_naissance', 'telephone', 'adresse',
            'type_beneficiaire', 'assure_principal', 'lien_parente', 'plan_couverture',
        ]
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        type_beneficiaire = cleaned_data.get('type_beneficiaire')
        assure_principal = cleaned_data.get('assure_principal')

        if assure_principal and self.instance.pk and assure_principal.pk == self.instance.pk:
            self.add_error('assure_principal', "Un patient ne peut pas être son propre assuré principal.")
        elif type_beneficiaire == Patient.TypeBeneficiaire.PRINCIPAL and assure_principal:
            self.add_error(
                'assure_principal',
                "Un assuré principal ne doit pas avoir son propre assuré principal renseigné.",
            )
        elif type_beneficiaire == Patient.TypeBeneficiaire.AYANT_DROIT and not assure_principal:
            self.add_error(
                'assure_principal',
                "Un ayant droit doit être rattaché à un assuré principal.",
            )
        return cleaned_data


class PatientCreationForm(PatientForm):
    """
    Creation d'un patient par l'administrateur (ajouter_patient).

    Ajoute un champ email transitoire (non stocke sur Patient, qui n'a pas
    d'email) : pour un assure principal, il sert a creer son compte de
    connexion (comme pour Medecin/Pharmacien) ; pour un ayant droit, il est
    ignore (les ayants droit n'ont pas de compte propre, geres par leur
    assure principal).
    """

    email = forms.EmailField(
        required=False,
        label='Email',
        help_text="Requis uniquement pour un assuré principal : sert à créer son compte de connexion.",
    )

    def clean(self):
        cleaned_data = super().clean()
        type_beneficiaire = cleaned_data.get('type_beneficiaire')
        email = cleaned_data.get('email')

        if type_beneficiaire == Patient.TypeBeneficiaire.PRINCIPAL:
            if not email:
                self.add_error('email', "L'email est requis pour un assuré principal (création du compte).")
            elif User.objects.filter(email=email).exists():
                self.add_error('email', "Cet email est déjà utilisé par un compte existant.")
        return cleaned_data


class EnvoyerNotificationForm(forms.Form):
    """Envoi d'une notification a un utilisateur precis ou a tout un role."""

    destinataire = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        label='Utilisateur précis (optionnel)',
        help_text="Laisser vide et choisir un rôle ci-dessous pour notifier tout un groupe.",
    )
    role = forms.ChoiceField(
        choices=[('', '---')] + list(User.Role.choices),
        required=False,
        label='Ou : tous les utilisateurs de ce rôle',
    )
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), label='Message')

    def clean(self):
        cleaned_data = super().clean()
        destinataire = cleaned_data.get('destinataire')
        role = cleaned_data.get('role')
        if not destinataire and not role:
            raise forms.ValidationError('Choisissez soit un utilisateur précis, soit un rôle.')
        if destinataire and role:
            raise forms.ValidationError('Choisissez un utilisateur précis OU un rôle, pas les deux.')
        return cleaned_data


class MedecinForm(forms.ModelForm):
    """
    Creation/modification d'un medecin par l'administrateur.

    A la creation, un compte de connexion (role MEDECIN) est cree
    automatiquement avec cet email (voir la vue ajouter_medecin) : c'est
    pourquoi l'email doit aussi etre libre cote User, pas seulement cote
    Medecin.
    """

    class Meta:
        model = Medecin
        fields = ['nom', 'prenom', 'specialite', 'telephone', 'email', 'prestataire']

    def clean_email(self):
        email = self.cleaned_data['email']
        comptes = User.objects.filter(email=email)
        if self.instance.pk and self.instance.user_id:
            comptes = comptes.exclude(pk=self.instance.user_id)
        if comptes.exists():
            raise forms.ValidationError("Cet email est déjà utilisé par un compte existant.")
        return email


class ServiceMedicalForm(forms.ModelForm):
    """Creation/modification d'un acte medical tarife."""

    class Meta:
        model = ServiceMedical
        fields = ['nom', 'description', 'prix', 'prestataire']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class PriseEnChargeForm(forms.ModelForm):
    """Creation/modification d'une prise en charge (par l'administrateur)."""

    class Meta:
        model = PriseEnCharge
        fields = ['patient', 'motif', 'statut']
        widgets = {
            'motif': forms.Textarea(attrs={'rows': 3}),
        }


class PlanCouvertureForm(forms.ModelForm):
    """Creation/modification d'un plan de couverture (par l'administrateur)."""

    class Meta:
        model = PlanCouverture
        fields = ['nom', 'taux_couverture', 'plafond_annuel']


class PaiementReglementForm(forms.ModelForm):
    """Marque un paiement comme regle (par l'administrateur)."""

    class Meta:
        model = Paiement
        fields = ['mode_reglement']

    def clean_mode_reglement(self):
        mode_reglement = self.cleaned_data['mode_reglement']
        if not mode_reglement:
            raise forms.ValidationError("Le mode de règlement est obligatoire.")
        return mode_reglement
