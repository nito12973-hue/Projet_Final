import datetime
import secrets
import string

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, password_validation
from django.db.models import Q
from django.utils import timezone

from .models import (
    Consultation,
    DemandeSupport,
    JournalActivite,
    LigneOrdonnance,
    Medecin,
    MessageSupport,
    Ordonnance,
    Paiement,
    Patient,
    Pharmacien,
    PlanCouverture,
    PreferenceNotification,
    Prestataire,
    PriseEnCharge,
    RendezVous,
    ServiceMedical,
    TentativeConnexion,
    User,
    valider_telephone,
)

# Les seuils vivent sur TentativeConnexion (modele) : une seule source.
# Alias conserves pour ne pas casser d'eventuels imports existants.
MAX_TENTATIVES_CONNEXION = TentativeConnexion.MAX_TENTATIVES
DUREE_BLOCAGE_SECONDES = int(TentativeConnexion.DUREE_BLOCAGE.total_seconds())


def generer_mot_de_passe():
    """Genere un mot de passe temporaire aleatoire (creation ou reinitialisation)."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(12))


class FormControlMixin:
    """
    Mixin qui applique automatiquement class="form-control" à tous les champs
    d'un formulaire, sauf les champs déjà dotés d'une classe CSS explicite.

    Utilisation : faire hériter le formulaire de FormControlMixin (en premier),
    puis de forms.ModelForm ou forms.Form.

    Exemple : class MonForm(FormControlMixin, forms.ModelForm): ...
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            # Les CheckboxInput, HiddenInput et MultiWidget ont un rendu
            # différent ; on ne leur applique pas form-control.
            if isinstance(widget, (forms.CheckboxInput, forms.HiddenInput,
                                   forms.CheckboxSelectMultiple, forms.MultiWidget)):
                continue
            css_actuel = widget.attrs.get('class', '')
            if 'form-control' not in css_actuel:
                widget.attrs['class'] = ('form-control ' + css_actuel).strip()


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


def aligner_patient_vers_user(patient):
    """La source métier Patient met à jour l'identité d'affichage du compte User (Nom/Prénom uniquement)."""
    if patient.user_id:
        user = patient.user
        modifs = []
        if patient.prenom and user.first_name != patient.prenom:
            user.first_name = patient.prenom
            modifs.append('first_name')
        if patient.nom and user.last_name != patient.nom:
            user.last_name = patient.nom
            modifs.append('last_name')
        if modifs:
            user.save(update_fields=modifs)


def aligner_medecin_vers_user(medecin):
    """La source métier Medecin met à jour l'identité d'affichage du compte User (Nom/Prénom uniquement)."""
    if medecin.user_id:
        user = medecin.user
        modifs = []
        if medecin.prenom and user.first_name != medecin.prenom:
            user.first_name = medecin.prenom
            modifs.append('first_name')
        if medecin.nom and user.last_name != medecin.nom:
            user.last_name = medecin.nom
            modifs.append('last_name')
        if modifs:
            user.save(update_fields=modifs)


from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm


class MotDePasseReinitialiserForm(FormControlMixin, SetPasswordForm):
    """Formulaire de définition du nouveau mot de passe avec styling form-control."""
    pass


class ChangerMotDePasseForm(FormControlMixin, PasswordChangeForm):
    """Formulaire de changement de mot de passe connecté avec styling form-control."""
    pass


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
            # Etat de blocage lu en base (TentativeConnexion) et non plus
            # dans le cache : meme regle, meme duree, mais consultable par
            # l'administrateur et coherent entre processus.
            if TentativeConnexion.bloque(email):
                raise forms.ValidationError(
                    'Trop de tentatives de connexion. Réessayez dans quelques minutes.'
                )

            self.user = authenticate(self.request, username=email, password=password)
            if self.user is None:
                ligne = TentativeConnexion.enregistrer_echec(email)
                if ligne.tentatives == TentativeConnexion.MAX_TENTATIVES:
                    utilisateur_existant = User.objects.filter(email=email.lower()).first()
                    if utilisateur_existant:
                        JournalActivite.objects.create(
                            auteur=None,
                            auteur_libelle="Système (sécurité)",
                            action=JournalActivite.Action.MODIFICATION,
                            objet=f"Utilisateur {utilisateur_existant.email}",
                            details="Compte temporairement bloqué (5 échecs consécutifs)",
                        )
                raise forms.ValidationError(
                    'Email ou mot de passe incorrect.'
                )
            TentativeConnexion.reussite(email)
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


class ConsultationForm(forms.ModelForm):
    """Creation d'une consultation sur rendez-vous par le medecin connecte."""

    date_consultation = forms.DateTimeField(
        label='Date de consultation',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        input_formats=[
            '%Y-%m-%dT%H:%M',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y %H:%M',
            '%d/%m/%Y %H:%M:%S',
        ],
    )

    class Meta:
        model = Consultation
        fields = ['patient', 'service', 'prise_en_charge', 'date_consultation', 'diagnostic', 'traitement']

    def __init__(self, *args, medecin=None, rdv=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.medecin = medecin
        self.rdv = rdv
        prestataire_effectif = (medecin.prestataire if medecin else None) or (rdv.prestataire if rdv else None)
        if prestataire_effectif:
            self.fields['service'].queryset = ServiceMedical.objects.filter(
                Q(prestataire=prestataire_effectif, prestataire__partenaire=True) | Q(prestataire__isnull=True)
            )
        elif medecin:
            self.fields['service'].queryset = ServiceMedical.objects.filter(prestataire__isnull=True)
        if 'service' in self.fields:
            self.fields['service'].error_messages['invalid_choice'] = "Ce service médical n'appartient pas à votre établissement."

        patient_cible = None
        if rdv and getattr(rdv, "patient", None):
            patient_cible = rdv.patient
        elif 'patient' in self.initial:
            p_val = self.initial['patient']
            if isinstance(p_val, Patient):
                patient_cible = p_val
            elif str(p_val).isdigit():
                patient_cible = Patient.objects.filter(pk=p_val).first()
        elif getattr(self.instance, "patient_id", None):
            patient_cible = self.instance.patient
        elif self.data and self.data.get('patient'):
            p_id = self.data.get('patient')
            if str(p_id).isdigit():
                patient_cible = Patient.objects.filter(pk=p_id).first()

        if 'prise_en_charge' in self.fields and patient_cible:
            qs = PriseEnCharge.objects.filter(
                patient=patient_cible,
                statut__in=["validee", "en_attente"],
            ).order_by("-date_demande")
            self.fields['prise_en_charge'].queryset = qs
            if not self.is_bound and not self.initial.get('prise_en_charge'):
                pec_validee = qs.filter(statut="validee").first()
                if pec_validee:
                    self.fields['prise_en_charge'].initial = pec_validee.pk

    def clean_service(self):
        service = self.cleaned_data.get('service')
        prestataire_effectif = (self.medecin.prestataire if self.medecin else None) or (self.rdv.prestataire if self.rdv else None)
        if service and service.prestataire:
            if not prestataire_effectif or service.prestataire != prestataire_effectif:
                raise forms.ValidationError("Ce service médical n'appartient pas à votre établissement.")
            if not service.prestataire.partenaire:
                raise forms.ValidationError("Ce service médical appartient à un établissement non partenaire.")
        return service


class ConsultationSpontaneeForm(ConsultationForm):
    """Creation d'une consultation spontanee ou d'urgence (sans rendez-vous)."""

    contexte_admission = forms.ChoiceField(
        choices=[
            ("", "--- Sélectionnez le contexte d'admission ---"),
            ("URGENCE", "Urgence médicale"),
            ("PASSAGE_SPONTANE", "Passage spontané non programmé"),
        ],
        label="Contexte d'admission",
        required=True,
        error_messages={
            "required": "Le contexte d'admission (Urgence ou Passage spontané) est obligatoire."
        },
    )
    numero_carte = forms.CharField(
        label="Numéro de carte de prise en charge",
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Ex : SN-XXXXXXXXXX'}),
        help_text="Vérification de concordance de carte : numéro figurant sur la carte physique de l'assuré.",
    )

    class Meta(ConsultationForm.Meta):
        fields = [
            'patient',
            'numero_carte',
            'contexte_admission',
            'service',
            'prise_en_charge',
            'date_consultation',
            'diagnostic',
            'traitement',
        ]

    def clean(self):
        cleaned_data = super().clean()
        contexte = cleaned_data.get('contexte_admission')
        if contexte and contexte not in ("URGENCE", "PASSAGE_SPONTANE"):
            self.add_error('contexte_admission', "Le contexte d'admission (Urgence ou Passage spontané) est obligatoire.")

        carte = (cleaned_data.get('numero_carte') or '').strip()
        patient = cleaned_data.get('patient')

        if not carte:
            self.add_error('numero_carte', "Le numéro de carte est obligatoire pour une consultation spontanée.")
        else:
            patient_carte = Patient.objects.filter(numero_carte__iexact=carte).first()
            if not patient_carte:
                self.add_error('numero_carte', "Aucun assuré ne correspond à ce numéro de carte de prise en charge.")
            elif patient and patient != patient_carte:
                self.add_error('numero_carte', "Le numéro de carte saisi ne correspond pas au patient sélectionné.")
            elif not patient and patient_carte:
                cleaned_data['patient'] = patient_carte

        return cleaned_data


class LigneOrdonnanceForm(forms.ModelForm):
    """Une ligne de prescription.

    medicament est le SEUL champ obligatoire. Imposer une posologie ou une
    duree pousserait le medecin a remplir du vide pour passer la validation :
    c'est ainsi qu'on fabrique de la fausse donnee medicale. Rien n'est
    complete automatiquement -- ce qui est enregistre est ce qu'il a saisi.
    """

    class Meta:
        model = LigneOrdonnance
        fields = ["medicament", "dosage", "posologie", "duree", "quantite"]
        widgets = {
            "medicament": forms.TextInput(attrs={"placeholder": "Nom du médicament"}),
            "dosage": forms.TextInput(attrs={"placeholder": "500 mg"}),
            "posologie": forms.TextInput(attrs={"placeholder": "3 fois par jour"}),
            "duree": forms.TextInput(attrs={"placeholder": "5 jours"}),
            "quantite": forms.TextInput(attrs={"placeholder": "1 boîte"}),
        }


class LigneOrdonnanceBaseFormSet(forms.BaseInlineFormSet):
    """Une ordonnance sans aucun medicament n'a pas de sens."""

    def clean(self):
        super().clean()
        if any(self.errors):
            return
        remplies = [
            f for f in self.forms
            if f.cleaned_data
            and not f.cleaned_data.get("DELETE")
            and f.cleaned_data.get("medicament")
        ]
        if not remplies:
            raise forms.ValidationError(
                "Ajoutez au moins un médicament à l'ordonnance."
            )


# extra=1 : le medecin arrive sur UNE ligne vide, pas sur un formulaire
# intimidant. can_delete permet de retirer une ligne par le mecanisme Django
# plutot que par le navigateur seul.
LigneOrdonnanceFormSet = forms.inlineformset_factory(
    Ordonnance,
    LigneOrdonnance,
    form=LigneOrdonnanceForm,
    formset=LigneOrdonnanceBaseFormSet,
    extra=1,
    can_delete=True,
)


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
    """Le medecin modifie ses informations professionnelles (pas email/role, geres par l'admin)."""

    class Meta:
        model = Medecin
        fields = ['specialite', 'prestataire', 'telephone', 'annees_experience', 'presentation']
        widgets = {
            'presentation': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': "Domaines de prise en charge, parcours, langues parlées...",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'prestataire' in self.fields:
            qs = Prestataire.objects.filter(partenaire=True)
            if self.instance and self.instance.prestataire_id:
                qs = Prestataire.objects.filter(Q(partenaire=True) | Q(pk=self.instance.prestataire_id))
            self.fields['prestataire'].queryset = qs.order_by('nom')
            self.fields['prestataire'].empty_label = "--- Aucun établissement rattaché ---"
            self.fields['prestataire'].required = False


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
            'adresse': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Adresse de résidence (ex: Médina, Dakar)'}),
        }
        labels = {
            'nom': 'Nom de famille',
            'prenom': 'Prénom(s)',
            'date_naissance': 'Date de naissance',
            'telephone': 'Numéro de téléphone',
            'adresse': 'Adresse de résidence',
        }

    def clean_date_naissance(self):
        """La date de naissance ne peut pas être dans le futur."""
        date_naissance = self.cleaned_data.get('date_naissance')
        if date_naissance and date_naissance > datetime.date.today():
            raise forms.ValidationError(
                "La date de naissance ne peut pas être dans le futur."
            )
        return date_naissance

    def save(self, commit=True):
        patient = super().save(commit=commit)
        if commit:
            aligner_patient_vers_user(patient)
        return patient


class AyantDroitForm(forms.ModelForm):
    """Creation/modification d'un ayant droit par l'assure principal."""

    class Meta:
        model = Patient
        fields = [
            'nom', 'prenom', 'date_naissance', 'telephone', 'adresse',
            'lien_parente', 'document_justificatif'
        ]
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'document_justificatif': 'Pièce justificative officielle (Extrait de naissance, acte de mariage - PDF/Image)',
        }
        help_texts = {
            'document_justificatif': 'Document requis pour la validation administrative par l\'IPM (taille max: 10 Mo).',
        }

    def __init__(self, *args, assure_principal=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.assure_principal = assure_principal or getattr(self.instance, 'assure_principal', None)

    def clean_date_naissance(self):
        """La date de naissance ne peut pas être dans le futur."""
        date_naissance = self.cleaned_data.get('date_naissance')
        if date_naissance and date_naissance > datetime.date.today():
            raise forms.ValidationError(
                "La date de naissance ne peut pas être dans le futur."
            )
        return date_naissance

    def clean_document_justificatif(self):
        doc = self.cleaned_data.get('document_justificatif')
        if doc and hasattr(doc, 'size') and doc.size > 10 * 1024 * 1024:
            raise forms.ValidationError("Le document justificatif ne doit pas dépasser 10 Mo.")
        return doc

    def clean(self):
        cleaned_data = super().clean()
        if not self.assure_principal:
            return cleaned_data

        lien_parente = cleaned_data.get('lien_parente')
        max_total = getattr(settings, 'MAX_AYANTS_DROIT_PAR_ASSURE', 6)
        max_conjoints = getattr(settings, 'MAX_CONJOINTS_PAR_ASSURE', 4)
        max_enfants = getattr(settings, 'MAX_ENFANTS_PAR_ASSURE', 6)

        # Verification du quota total lors de l'ajout d'un nouvel ayant droit
        if not self.instance.pk:
            nb_actuel = self.assure_principal.ayants_droit.count()
            if nb_actuel >= max_total:
                raise forms.ValidationError(
                    f"Quota atteint : Vous ne pouvez pas inscrire plus de {max_total} ayants droit sous votre contrat IPM. "
                    "Veuillez contacter le gestionnaire IPM pour toute dérogation."
                )

        # Verification des quotas par catégorie
        if lien_parente == Patient.LienParente.CONJOINT:
            qs_conjoints = self.assure_principal.ayants_droit.filter(lien_parente=Patient.LienParente.CONJOINT)
            if self.instance.pk:
                qs_conjoints = qs_conjoints.exclude(pk=self.instance.pk)
            if qs_conjoints.count() >= max_conjoints:
                raise forms.ValidationError(
                    f"Limite atteinte : Le nombre maximal de conjoints déclarés est de {max_conjoints} (selon le Code de la famille)."
                )
        elif lien_parente == Patient.LienParente.ENFANT:
            qs_enfants = self.assure_principal.ayants_droit.filter(lien_parente=Patient.LienParente.ENFANT)
            if self.instance.pk:
                qs_enfants = qs_enfants.exclude(pk=self.instance.pk)
            if qs_enfants.count() >= max_enfants:
                raise forms.ValidationError(
                    f"Limite atteinte : Le nombre maximal d'enfants déclarés sous ce contrat est de {max_enfants}."
                )

        return cleaned_data


class RendezVousAssureForm(forms.ModelForm):
    """Demande de rendez-vous par l'assure, pour lui-meme ou un ayant droit."""

    medecin = forms.ModelChoiceField(
        queryset=Medecin.objects.filter(Q(user__is_active=True) | Q(user__isnull=True)),
        label='Médecin',
    )
    prestataire = forms.ModelChoiceField(
        queryset=Prestataire.objects.filter(partenaire=True).exclude(type_prestataire=Prestataire.Type.PHARMACIE),
        required=False,
        label='Établissement de soins (Hôpital, Clinique, Cabinet)',
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
        widgets = {
            'motif': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': (
                    "Ex. : douleurs abdominales depuis trois jours, "
                    "avec de la fievre et des nausees."
                ),
            }),
        }
        help_texts = {
            'motif': "Decrivez ce que vous ressentez. Le medecin etablira le diagnostic.",
        }

    def __init__(self, *args, beneficiaires=None, prestataire=None, **kwargs):
        super().__init__(*args, **kwargs)
        if beneficiaires is not None:
            self.fields['patient'].queryset = beneficiaires

        # Le parcours passe par le prestataire : quand il est connu, on ne
        # propose QUE ses medecins actifs (ou sans compte specifique).
        actif_ou_sans_compte = Q(user__is_active=True) | Q(user__isnull=True)
        if prestataire is not None:
            # Les medecins SANS structure restent proposes : tant que
            # l'administrateur ne leur en a pas attribue une, les exclure les
            # rendrait introuvables et bloquerait toute demande de
            # rendez-vous. C'est exactement ce qui se produisait.
            self.fields['medecin'].queryset = Medecin.objects.filter(
                Q(prestataire=prestataire) | Q(prestataire__isnull=True)
            ).filter(
                actif_ou_sans_compte
            ).order_by('nom', 'prenom')
            self.fields['prestataire'].initial = prestataire
        else:
            self.fields['medecin'].queryset = Medecin.objects.filter(
                actif_ou_sans_compte
            ).select_related(
                'prestataire'
            ).order_by('nom', 'prenom')

    def clean_patient(self):
        patient = self.cleaned_data.get('patient')
        if patient and not patient.est_valide:
            raise forms.ValidationError(
                "Ce bénéficiaire est en cours d'instruction administrative. Seuls les bénéficiaires validés par l'IPM peuvent prendre rendez-vous."
            )
        return patient

    def clean_date_heure(self):
        date_heure = self.cleaned_data['date_heure']
        if date_heure < timezone.now():
            raise forms.ValidationError("La date et l'heure du rendez-vous ne peuvent pas être dans le passé.")

        heure_locale = timezone.localtime(date_heure) if timezone.is_aware(date_heure) else date_heure
        if heure_locale.weekday() == 6:
            raise forms.ValidationError(
                "Les prises de rendez-vous en ligne ne sont pas assurées le dimanche (fermeture des consultations programmées). En cas d'urgence, veuillez vous présenter directement au service d'accueil."
            )
        if heure_locale.hour < 8 or (heure_locale.hour >= 19 and (heure_locale.minute > 0 or heure_locale.hour > 19)):
            raise forms.ValidationError(
                "Les rendez-vous sont planifiables uniquement pendant les heures d'ouverture (de 08h00 à 19h00)."
            )
        return date_heure

    def clean(self):
        """Le medecin doit exercer chez le prestataire choisi.

        Regle posee ici et non dans le modele : un rendez-vous cree par
        l'administration ou une reprise de donnees peut legitimement porter
        un prestataire different (medecin ayant change de structure depuis).
        C'est la DEMANDE de l'assure qu'on contraint, pas l'historique.
        """
        cleaned = super().clean()
        medecin = cleaned.get('medecin')
        prestataire = cleaned.get('prestataire')
        # Un rendez-vous ne peut en aucun cas être pris dans une pharmacie
        if prestataire and prestataire.type_prestataire == Prestataire.Type.PHARMACIE:
            self.add_error('prestataire', forms.ValidationError(
                "Les rendez-vous médicaux ne peuvent pas être pris dans une pharmacie. Les pharmacies assurent uniquement la délivrance d'ordonnances."
            ))

        # Si l'assuré n'a pas sélectionné de prestataire mais que le médecin est rattaché
        # à une structure, on déduit et affecte automatiquement ce prestataire.
        if not prestataire and medecin and medecin.prestataire_id is not None:
            prestataire = medecin.prestataire
            cleaned['prestataire'] = prestataire

        # `medecin.prestataire_id is not None` est indispensable : un medecin
        # sans structure n'est en contradiction avec aucun prestataire. Sans
        # cette condition, il etait refuse partout.
        if (medecin and prestataire and medecin.prestataire_id is not None
                and medecin.prestataire_id != prestataire.pk):
            self.add_error('medecin', forms.ValidationError(
                "Ce medecin n'exerce pas chez %(prestataire)s.",
                params={'prestataire': prestataire.nom},
            ))
        return cleaned


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

    def clean_date_naissance(self):
        """La date de naissance ne peut pas être dans le futur."""
        date_naissance = self.cleaned_data.get('date_naissance')
        if date_naissance and date_naissance > datetime.date.today():
            raise forms.ValidationError(
                "La date de naissance ne peut pas être dans le futur."
            )
        return date_naissance

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

    def save(self, commit=True):
        patient = super().save(commit=commit)
        if commit:
            aligner_patient_vers_user(patient)
        return patient


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
        fields = [
            'nom', 'prenom', 'specialite', 'telephone', 'email', 'prestataire',
            'annees_experience', 'presentation',
        ]
        widgets = {
            'presentation': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': "Domaines de prise en charge, parcours, langues parlees...",
            }),
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        comptes = User.objects.filter(email=email)
        if self.instance.pk and self.instance.user_id:
            comptes = comptes.exclude(pk=self.instance.user_id)
        if comptes.exists():
            raise forms.ValidationError("Cet email est déjà utilisé par un compte existant.")
        return email

    def save(self, commit=True):
        medecin = super().save(commit=commit)
        if commit:
            aligner_medecin_vers_user(medecin)
        return medecin


class ServiceMedicalForm(forms.ModelForm):
    """Creation/modification d'un acte medical tarife."""

    class Meta:
        model = ServiceMedical
        fields = ['nom', 'description', 'prix', 'prestataire']
        labels = {
            'nom': "Nom de l'acte / service médical",
            'description': "Description",
            'prix': "Tarif conventionné (FCFA)",
            'prestataire': "Établissement conventionné (optionnel)",
        }
        help_texts = {
            'prestataire': "Laissez vide si ce tarif s'applique à l'ensemble du réseau conventionné.",
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class PriseEnChargeForm(forms.ModelForm):
    """Creation/modification d'une prise en charge (par l'administrateur)."""

    class Meta:
        model = PriseEnCharge
        fields = ['patient', 'devis_fichier', 'montant_estime', 'motif', 'statut', 'motif_refus']
        labels = {
            'patient': "Bénéficiaire des soins",
            'devis_fichier': "Pièce jointe du devis (PDF ou photo/scan)",
            'montant_estime': "Montant estimé du devis (FCFA)",
            'motif': "Devis estimatif / Détails des actes (optionnel si document joint)",
            'statut': "Statut de la prise en charge",
            'motif_refus': "Motif du refus (si refusé)",
        }
        widgets = {
            'motif': forms.Textarea(attrs={'rows': 3, 'placeholder': "Optionnel si un fichier est joint. Détails des actes prévus ou devis..."}),
            'montant_estime': forms.NumberInput(attrs={'placeholder': 'Ex : 250000', 'min': '0', 'step': '500'}),
            'devis_fichier': forms.FileInput(attrs={'accept': '.pdf,image/*'}),
            'motif_refus': forms.TextInput(attrs={'placeholder': 'Motif obligatoire en cas de refus'}),
        }
        help_texts = {
            'devis_fichier': "Format accepté : PDF ou image (PNG, JPG) - taille maximale : 10 Mo.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['motif'].required = False
        self.fields['montant_estime'].required = False
        self.fields['devis_fichier'].required = False

    def clean_devis_fichier(self):
        doc = self.cleaned_data.get('devis_fichier')
        if doc and hasattr(doc, 'size') and doc.size > 10 * 1024 * 1024:
            raise forms.ValidationError("Le fichier du devis ne doit pas dépasser 10 Mo.")
        return doc


class DemandePriseEnChargeAssureForm(forms.ModelForm):
    """Demande de prise en charge soumise par un assure pour lui ou ses ayants droit."""

    class Meta:
        model = PriseEnCharge
        fields = ['patient', 'devis_fichier', 'montant_estime', 'motif']
        labels = {
            'patient': "Bénéficiaire des soins",
            'devis_fichier': "Fichier du devis médical (PDF ou photo/scan)",
            'montant_estime': "Montant figurant sur le devis (FCFA)",
            'motif': "Remarques ou précisions complémentaires (optionnel)",
        }
        widgets = {
            'motif': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Facultatif : vous pouvez laisser ce champ vide si tous les actes et détails figurent déjà sur votre devis numérisé ci-dessus.'
            }),
            'montant_estime': forms.NumberInput(attrs={'placeholder': 'Ex : 150000', 'min': '0', 'step': '500'}),
            'devis_fichier': forms.FileInput(attrs={'accept': '.pdf,image/*'}),
        }
        help_texts = {
            'devis_fichier': "Téléversez simplement votre devis (PDF, scan ou photo - max 10 Mo). Inutile de tout recopier manuellement !",
            'montant_estime': "Indiquez le montant estimatif pour accélérer le calcul automatique de votre prise en charge.",
        }

    def __init__(self, *args, assure_patient=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['motif'].required = False
        self.fields['montant_estime'].required = False
        self.fields['devis_fichier'].required = False
        if assure_patient:
            membres_valides = [assure_patient.pk] + list(
                assure_patient.ayants_droit.filter(
                    statut_validation=Patient.StatutValidation.VALIDE
                ).values_list('pk', flat=True)
            )
            self.fields['patient'].queryset = Patient.objects.filter(pk__in=membres_valides)
            self.fields['patient'].empty_label = None

    def clean_devis_fichier(self):
        doc = self.cleaned_data.get('devis_fichier')
        if doc and hasattr(doc, 'size') and doc.size > 10 * 1024 * 1024:
            raise forms.ValidationError("Le fichier du devis ne doit pas dépasser 10 Mo.")
        return doc

    def clean_patient(self):
        patient = self.cleaned_data.get('patient')
        if patient and not patient.est_valide:
            raise forms.ValidationError(
                "Ce bénéficiaire est en attente de validation par l'administration IPM et ne peut pas faire l'objet d'une prise en charge."
            )
        return patient

    def clean(self):
        cleaned_data = super().clean()
        fichier = cleaned_data.get('devis_fichier')
        motif = (cleaned_data.get('motif') or '').strip()
        if not fichier and not motif:
            raise forms.ValidationError(
                "Veuillez joindre le document/photo de votre devis ou renseigner une description des actes prévus."
            )
        return cleaned_data



class PlanCouvertureForm(forms.ModelForm):
    """Creation/modification d'un plan de couverture (par l'administrateur)."""

    class Meta:
        model = PlanCouverture
        fields = ['nom', 'taux_couverture', 'plafond_annuel']
        labels = {
            'nom': "Nom du plan de couverture",
            'taux_couverture': "Taux de prise en charge (%)",
            'plafond_annuel': "Plafond annuel de remboursement (FCFA)",
        }
        help_texts = {
            'taux_couverture': "Pourcentage des frais pris en charge par l'assurance (ex: 80 pour 80%).",
            'plafond_annuel': "Laissez vide pour une couverture sans plafond annuel.",
        }


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


class MonCompteForm(forms.ModelForm):
    """Modification par l'utilisateur de ses propres informations (tous roles).

    Le role n'y figure pas : regle metier du projet, il est stocke en base et
    n'est jamais choisi par l'utilisateur. L'email, lui, est l'identifiant de
    connexion (USERNAME_FIELD) : le changer revient a changer sa facon de se
    connecter, donc on exige le mot de passe actuel pour confirmer -- mais
    seulement dans ce cas, pour ne pas alourdir une simple correction de nom.
    """

    mot_de_passe_actuel = forms.CharField(
        label="Mot de passe actuel",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
        required=False,
        help_text="Requis uniquement pour changer l'adresse email.",
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone_number", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.email_initial = self.instance.email

    def clean_phone_number(self):
        telephone = self.cleaned_data.get("phone_number", "").strip()
        if telephone:
            valider_telephone(telephone)
        return telephone

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if not email:
            raise forms.ValidationError("L'adresse email est obligatoire.")
        # iexact : deux comptes ne doivent pas differer que par la casse.
        doublon = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if doublon.exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email

    def clean(self):
        donnees = super().clean()
        email = donnees.get("email")
        if email and email.lower() != self.email_initial.lower():
            mot_de_passe = donnees.get("mot_de_passe_actuel")
            if not mot_de_passe:
                self.add_error(
                    "mot_de_passe_actuel",
                    "Indiquez votre mot de passe actuel pour changer d'adresse email.",
                )
            elif not self.instance.check_password(mot_de_passe):
                self.add_error("mot_de_passe_actuel", "Mot de passe incorrect.")
        return donnees

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            if user.role == User.Role.ASSURE and hasattr(user, 'patient') and user.patient:
                patient = user.patient
                modifs_patient = []
                if user.first_name and patient.prenom != user.first_name:
                    patient.prenom = user.first_name
                    modifs_patient.append('prenom')
                if user.last_name and patient.nom != user.last_name:
                    patient.nom = user.last_name
                    modifs_patient.append('nom')
                if modifs_patient:
                    patient.save(update_fields=modifs_patient)

            elif user.role == User.Role.MEDECIN and hasattr(user, 'medecin') and user.medecin:
                medecin = user.medecin
                modifs_medecin = []
                if user.first_name and medecin.prenom != user.first_name:
                    medecin.prenom = user.first_name
                    modifs_medecin.append('prenom')
                if user.last_name and medecin.nom != user.last_name:
                    medecin.nom = user.last_name
                    modifs_medecin.append('nom')
                if modifs_medecin:
                    medecin.save(update_fields=modifs_medecin)
        return user


class PreferenceNotificationForm(forms.ModelForm):
    class Meta:
        model = PreferenceNotification
        fields = [
            "email_rdv",
            "email_prise_en_charge",
            "email_ordonnance",
            "email_delivrance",
        ]
        labels = {
            "email_rdv": "Mise à jour des rendez-vous",
            "email_prise_en_charge": "Validation / Refus de prise en charge",
            "email_ordonnance": "Émission d'ordonnance",
            "email_delivrance": "Avis de délivrance en pharmacie",
        }


class ActivationCompteForm(forms.Form):
    """Formulaire sécurisé pour définir son mot de passe initial lors de l'onboarding."""

    nouveau_mot_de_passe = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "placeholder": "Minimum 8 caractères"}),
        min_length=8,
        help_text="Choisissez un mot de passe robuste d'au moins 8 caractères.",
    )
    confirmation_mot_de_passe = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "placeholder": "Répétez le mot de passe"}),
    )

    def __init__(self, utilisateur, *args, **kwargs):
        self.utilisateur = utilisateur
        super().__init__(*args, **kwargs)

    def clean(self):
        donnees = super().clean()
        p1 = donnees.get("nouveau_mot_de_passe")
        p2 = donnees.get("confirmation_mot_de_passe")
        if p1 and p2 and p1 != p2:
            self.add_error("confirmation_mot_de_passe", "Les deux mots de passe ne correspondent pas.")
        return donnees

    def sauvegarder(self):
        mot_de_passe = self.cleaned_data["nouveau_mot_de_passe"]
        self.utilisateur.set_password(mot_de_passe)
        self.utilisateur.is_active = True
        self.utilisateur.save(update_fields=["password", "is_active"])
        return self.utilisateur


class DemandeSupportForm(forms.ModelForm):
    """Formulaire de création d'un ticket d'assistance par l'assuré."""

    premier_message = forms.CharField(
        label="Description détaillée de votre demande",
        widget=forms.Textarea(attrs={
            "rows": 5,
            "placeholder": "Expliquez précisément votre demande ou le problème rencontré afin que l'administration puisse vous assister efficacement..."
        }),
        help_text="Donnez un maximum de précisions utiles (dates, références de consultation, ordonnance ou nom de médecin si pertinent)."
    )

    class Meta:
        model = DemandeSupport
        fields = ["objet", "categorie", "priorite"]
        labels = {
            "objet": "Objet de la demande",
            "categorie": "Catégorie",
            "priorite": "Niveau d'urgence",
        }
        widgets = {
            "objet": forms.TextInput(attrs={"placeholder": "Ex. : Demande de clarification sur mon taux de couverture"}),
        }


class ReponseSupportForm(forms.ModelForm):
    """Formulaire d'ajout d'un message dans le fil de discussion support."""

    class Meta:
        model = MessageSupport
        fields = ["message"]
        labels = {"message": "Votre message"}
        widgets = {
            "message": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Écrivez votre réponse ici..."
            })
        }


