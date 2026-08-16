import datetime
import io
import uuid
from math import atan2, cos, radians, sin, sqrt

import qrcode
import qrcode.image.svg
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

valider_telephone = RegexValidator(
    regex=r'^\+?[0-9 \-]{7,20}$',
    message="Numero de telephone invalide (chiffres, espaces, tirets et + uniquement).",
)


def distance_km(lat1, lon1, lat2, lon2):
    """Distance a vol d'oiseau entre deux points, en kilometres (formule de haversine)."""
    rayon_terre_km = 6371.0
    phi1, phi2 = radians(lat1), radians(lat2)
    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)
    a = sin(delta_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2) ** 2
    return rayon_terre_km * 2 * atan2(sqrt(a), sqrt(1 - a))


class UserManager(BaseUserManager):
    """Manager du modèle User : l'email remplace le nom d'utilisateur."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', self.model.Role.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Un superutilisateur doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Un superutilisateur doit avoir is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modèle utilisateur unique de SantéSN.

    Règles métier :
    - authentification par email + mot de passe uniquement
    - le rôle est stocké en base et jamais choisi à la connexion
    - la redirection après connexion dépend du rôle
    """

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrateur'
        ASSURE = 'ASSURE', 'Assuré'
        MEDECIN = 'MEDECIN', 'Médecin'
        PHARMACIEN = 'PHARMACIEN', 'Pharmacien'

    email = models.EmailField('adresse email', unique=True)
    first_name = models.CharField('prénom', max_length=150, blank=True)
    last_name = models.CharField('nom', max_length=150, blank=True)
    phone_number = models.CharField('téléphone', max_length=20, blank=True)
    role = models.CharField(
        'rôle',
        max_length=20,
        choices=Role.choices,
        db_index=True,
    )

    is_staff = models.BooleanField('accès au back-office', default=False)
    is_active = models.BooleanField('compte actif', default=True)
    date_joined = models.DateTimeField('date de création', default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'utilisateur'
        verbose_name_plural = 'utilisateurs'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        full_name = self.get_full_name()
        return f'{full_name} ({self.email})' if full_name else self.email

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    def get_short_name(self):
        return self.first_name

    # Aides métier utilisées par les décorateurs et les templates
    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def is_assure(self):
        return self.role == self.Role.ASSURE

    @property
    def is_medecin(self):
        return self.role == self.Role.MEDECIN

    @property
    def is_pharmacien(self):
        return self.role == self.Role.PHARMACIEN


class PlanCouverture(models.Model):
    """Regle de remboursement appliquee a un assure et ses ayants droit."""

    nom = models.CharField(max_length=100)
    taux_couverture = models.DecimalField(
        "taux de couverture (%)",
        max_digits=5,
        decimal_places=2,
        help_text="Pourcentage des frais pris en charge par l'assurance (ex: 90.00 pour 90%).",
    )
    plafond_annuel = models.DecimalField(
        "plafond annuel",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "plan de couverture"
        verbose_name_plural = "plans de couverture"

    def __str__(self):
        return f"{self.nom} ({self.taux_couverture}%)"


class Prestataire(models.Model):
    """Etablissement de sante partenaire (hopital, clinique, pharmacie, cabinet)."""

    class Type(models.TextChoices):
        HOPITAL = "HOPITAL", "Hôpital"
        CLINIQUE = "CLINIQUE", "Clinique"
        PHARMACIE = "PHARMACIE", "Pharmacie"
        CABINET = "CABINET", "Cabinet médical"

    nom = models.CharField(max_length=150)
    type_prestataire = models.CharField(
        "type d'etablissement", max_length=20, choices=Type.choices
    )
    adresse = models.TextField(blank=True)
    ville = models.CharField(max_length=100, blank=True)
    telephone = models.CharField(max_length=20, blank=True, validators=[valider_telephone])
    partenaire = models.BooleanField(
        "partenaire actif", default=True, help_text="Fait partie du reseau conventionne."
    )
    date_conventionnement = models.DateField(null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="Renseignee en placant un point sur la carte (formulaire prestataire).",
    )
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name = "prestataire"
        verbose_name_plural = "prestataires"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} ({self.get_type_prestataire_display()})"


class Patient(models.Model):
    class TypeBeneficiaire(models.TextChoices):
        PRINCIPAL = "PRINCIPAL", "Assuré principal"
        AYANT_DROIT = "AYANT_DROIT", "Ayant droit"

    class LienParente(models.TextChoices):
        CONJOINT = "CONJOINT", "Conjoint(e)"
        ENFANT = "ENFANT", "Enfant"
        AUTRE = "AUTRE", "Autre"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patient",
        help_text="Compte de connexion associe (assure principal uniquement).",
    )
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    telephone = models.CharField(max_length=20, blank=True, validators=[valider_telephone])
    adresse = models.TextField(blank=True)

    type_beneficiaire = models.CharField(
        max_length=20,
        choices=TypeBeneficiaire.choices,
        default=TypeBeneficiaire.PRINCIPAL,
        db_index=True,
    )
    assure_principal = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ayants_droit",
        limit_choices_to={"type_beneficiaire": TypeBeneficiaire.PRINCIPAL},
        help_text="Renseigne uniquement pour un ayant droit : l'assure principal rattache.",
    )
    lien_parente = models.CharField(
        max_length=20, choices=LienParente.choices, blank=True, default=""
    )
    numero_carte = models.CharField(
        "numero de carte de prise en charge",
        max_length=30,
        unique=True,
        editable=False,
    )
    plan_couverture = models.ForeignKey(
        PlanCouverture,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="beneficiaires",
        help_text="Renseigne pour l'assure principal ; les ayants droit heritent de ce plan.",
    )

    class Meta:
        ordering = ["nom", "prenom"]

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    def save(self, *args, **kwargs):
        if not self.numero_carte:
            self.numero_carte = self._generer_numero_carte()
        super().save(*args, **kwargs)

    @staticmethod
    def _generer_numero_carte():
        return f"SN-{uuid.uuid4().hex[:10].upper()}"

    @property
    def est_ayant_droit(self):
        return self.type_beneficiaire == self.TypeBeneficiaire.AYANT_DROIT

    @property
    def titulaire(self):
        """Le beneficiaire porteur du plan de couverture (soi-meme si principal)."""
        return self.assure_principal if self.est_ayant_droit and self.assure_principal_id else self

    @property
    def taux_couverture(self):
        plan = self.titulaire.plan_couverture
        return plan.taux_couverture if plan else None


class Medecin(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medecin",
    )
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    specialite = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, validators=[valider_telephone])
    email = models.EmailField(unique=True)
    prestataire = models.ForeignKey(
        Prestataire,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medecins",
    )

    def __str__(self):
        return f"Dr {self.prenom} {self.nom}"


class Pharmacien(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pharmacien",
    )
    prestataire = models.ForeignKey(
        Prestataire,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pharmaciens",
    )

    class Meta:
        verbose_name = "pharmacien"
        verbose_name_plural = "pharmaciens"

    def __str__(self):
        if self.user:
            return self.user.get_full_name() or self.user.email
        return f"Pharmacien #{self.pk}"


class ServiceMedical(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    prestataire = models.ForeignKey(
        Prestataire,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="services",
    )

    def __str__(self):
        return self.nom


class PriseEnCharge(models.Model):
    STATUT_CHOICES = [
        ("en_attente", "En attente"),
        ("validee", "Validée"),
        ("refusee", "Refusée"),
        ("terminee", "Terminée"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    date_demande = models.DateTimeField(auto_now_add=True)
    motif = models.TextField()
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="en_attente",
        db_index=True,
    )

    def __str__(self):
        return f"Prise en charge de {self.patient} - {self.statut}"

    def clean(self):
        """Interdit de changer de patient une fois des consultations rattachees.

        Les consultations restent liees a la prise en charge : les reattribuer
        par ce biais donnerait a un assure les soins d'une autre personne
        (l'ecran "Mes prises en charge" affiche consultation_set, medecin et
        montants compris). Corriger une erreur de saisie reste possible tant
        qu'aucune consultation n'existe -- c'est le seul cas legitime.

        La regle vit ici et non dans le formulaire : /admin/ expose lui aussi
        ce champ, et les ModelForm des deux cotes appellent full_clean().
        """
        if not self.pk or self.patient_id is None:
            return
        patient_enregistre = (
            type(self).objects.filter(pk=self.pk)
            .values_list("patient_id", flat=True)
            .first()
        )
        if (
            patient_enregistre is not None
            and patient_enregistre != self.patient_id
            and self.consultation_set.exists()
        ):
            raise ValidationError({
                "patient": (
                    "Des consultations sont déjà rattachées à cette prise en "
                    "charge : la réattribuer donnerait ces soins à une autre "
                    "personne. Créez une nouvelle prise en charge."
                ),
            })


class Consultation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)
    service = models.ForeignKey(ServiceMedical, on_delete=models.SET_NULL, null=True, blank=True)
    prise_en_charge = models.ForeignKey(
        PriseEnCharge,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    date_consultation = models.DateTimeField()
    diagnostic = models.TextField()
    traitement = models.TextField(blank=True)

    def __str__(self):
        return f"Consultation de {self.patient} avec {self.medecin}"

    def clean(self):
        """La prise en charge liee doit appartenir au patient consulte.

        Regle deplacee de ConsultationForm vers le modele : /admin/ enregistre
        Consultation sans ModelAdmin dedie, donc le formulaire de l'app y etait
        purement et simplement contourne. La ValidationError est indexee par
        champ pour que le message s'affiche sous prise_en_charge, comme avant.
        """
        if (
            self.patient_id
            and self.prise_en_charge_id
            and self.prise_en_charge.patient_id != self.patient_id
        ):
            raise ValidationError({
                "prise_en_charge": (
                    "Cette prise en charge ne correspond pas au patient sélectionné."
                ),
            })


class Paiement(models.Model):
    """
    Suivi du reglement d'une consultation : montant total, repartition
    assurance/patient (calculee a partir du taux de couverture du plan si la
    prise en charge liee a la consultation est validee, sinon le patient
    regle 100% du montant), et statut de reglement.
    """

    class Statut(models.TextChoices):
        NON_REGLE = "non_regle", "Non réglé"
        REGLE = "regle", "Réglé"

    class ModeReglement(models.TextChoices):
        ESPECES = "ESPECES", "Espèces"
        MOBILE_MONEY = "MOBILE_MONEY", "Mobile money"
        CARTE = "CARTE", "Carte bancaire"
        VIREMENT = "VIREMENT", "Virement"

    consultation = models.OneToOneField(Consultation, on_delete=models.CASCADE, related_name="paiement")
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taux_applique = models.DecimalField(
        "taux de couverture applique (%)", max_digits=5, decimal_places=2, default=0
    )
    montant_part_assurance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    montant_part_patient = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.NON_REGLE, db_index=True)
    mode_reglement = models.CharField(max_length=20, choices=ModeReglement.choices, blank=True)
    date_reglement = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Paiement {self.get_statut_display()} - {self.consultation}"

    @classmethod
    def calculer_pour(cls, consultation):
        """Construit (sans sauvegarder) le Paiement correspondant a une consultation."""
        montant_total = consultation.service.prix if consultation.service_id else 0
        taux = 0
        prise_en_charge = consultation.prise_en_charge
        if prise_en_charge is not None and prise_en_charge.statut == "validee":
            taux = consultation.patient.taux_couverture or 0
        montant_part_assurance = montant_total * taux / 100
        montant_part_patient = montant_total - montant_part_assurance
        return cls(
            consultation=consultation,
            montant_total=montant_total,
            taux_applique=taux,
            montant_part_assurance=montant_part_assurance,
            montant_part_patient=montant_part_patient,
        )


class Ordonnance(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    medicaments = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    code_qr = models.CharField(
        "code de verification",
        max_length=20,
        unique=True,
        editable=False,
        help_text="Encode dans le QR scanne par la pharmacie pour valider l'ordonnance.",
    )

    def __str__(self):
        return f"Ordonnance du {self.date_creation:%d/%m/%Y}"

    def save(self, *args, **kwargs):
        if not self.code_qr:
            self.code_qr = self._generer_code_qr()
        super().save(*args, **kwargs)

    @staticmethod
    def _generer_code_qr():
        return f"RX-{uuid.uuid4().hex[:10].upper()}"

    @property
    def qr_svg(self):
        """QR code (SVG) encodant le code de verification, scanne par la pharmacie."""
        image = qrcode.make(self.code_qr, image_factory=qrcode.image.svg.SvgImage)
        buffer = io.BytesIO()
        image.save(buffer)
        return buffer.getvalue().decode("utf-8")


class RendezVous(models.Model):
    """Rendez-vous d'un patient avec un medecin, aupres d'un prestataire."""

    class Statut(models.TextChoices):
        DEMANDE = "DEMANDE", "Demande"
        CONFIRME = "CONFIRME", "Confirmé"
        ANNULE = "ANNULE", "Annulé"
        TERMINE = "TERMINE", "Terminé"

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="rendez_vous")
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE, related_name="rendez_vous")
    prestataire = models.ForeignKey(
        Prestataire,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rendez_vous",
    )
    date_heure = models.DateTimeField("date et heure")
    motif = models.CharField(max_length=255, blank=True)
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.DEMANDE,
        db_index=True,
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "rendez-vous"
        verbose_name_plural = "rendez-vous"
        ordering = ["date_heure"]

    def __str__(self):
        return f"RDV {self.patient} - Dr {self.medecin} ({self.date_heure:%d/%m/%Y %H:%M})"


class Delivrance(models.Model):
    """Delivrance d'une ordonnance par un pharmacien (une seule par ordonnance)."""

    ordonnance = models.OneToOneField(Ordonnance, on_delete=models.CASCADE, related_name="delivrance")
    pharmacien = models.ForeignKey(Pharmacien, on_delete=models.CASCADE, related_name="delivrances")
    date_delivrance = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "delivrance"
        verbose_name_plural = "delivrances"
        ordering = ["-date_delivrance"]

    def __str__(self):
        return f"Delivrance de {self.ordonnance} par {self.pharmacien}"


class Notification(models.Model):
    """
    Notification envoyee par un administrateur a un utilisateur precis.

    Pour notifier un role entier, l'administrateur cree une notification par
    destinataire (fan-out a la creation) : chaque utilisateur garde son propre
    statut de lecture, sans dependre des autres.
    """

    destinataire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    message = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    lue = models.BooleanField(default=False)

    class Meta:
        verbose_name = "notification"
        verbose_name_plural = "notifications"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"Notification pour {self.destinataire} ({self.date_creation:%d/%m/%Y})"


class TentativeConnexion(models.Model):
    """Compteur d'echecs de connexion et blocage temporaire, par adresse email.

    REMPLACE la cle de cache 'tentatives_connexion:{email}' utilisee jusqu'ici.
    Ce n'est pas un second systeme : c'est le meme, deplace la ou il peut etre
    LU. Le cache de Django n'offre aucun moyen d'enumerer ses cles ni de
    connaitre le temps restant, ce qui rendait impossible toute interface
    d'administration. Et sans configuration CACHES, le backend par defaut est
    LocMemCache : en production multi-processus, chaque worker avait son propre
    compteur -- 5 tentatives par worker, et deux administrateurs voyaient deux
    etats differents.

    La cle reste l'EMAIL SAISI, pas un compte : une adresse inexistante doit
    etre freinee elle aussi, sinon on offre un oracle permettant de deviner
    quelles adresses sont enregistrees. L'interface d'administration, elle,
    ne montre que les lignes correspondant a un compte reel.
    """

    MAX_TENTATIVES = 5
    DUREE_BLOCAGE = datetime.timedelta(minutes=5)

    email = models.EmailField("adresse saisie", unique=True, db_index=True)
    tentatives = models.PositiveSmallIntegerField("échecs consécutifs", default=0)
    dernier_echec = models.DateTimeField("dernier échec", auto_now=True)

    class Meta:
        verbose_name = "tentative de connexion"
        verbose_name_plural = "tentatives de connexion"
        ordering = ["-dernier_echec"]

    def __str__(self):
        return f"{self.email} ({self.tentatives} échec(s))"

    # -- lecture ------------------------------------------------------------

    @property
    def fin_blocage(self):
        return self.dernier_echec + self.DUREE_BLOCAGE

    def est_bloque(self, maintenant=None):
        """Bloque tant que le quota est atteint ET que le delai court encore.

        Le delai repart a chaque nouvel echec (auto_now sur dernier_echec) :
        c'est le comportement de l'ancien cache.set(), conserve tel quel.
        """
        maintenant = maintenant or timezone.now()
        return self.tentatives >= self.MAX_TENTATIVES and maintenant < self.fin_blocage

    def secondes_restantes(self, maintenant=None):
        maintenant = maintenant or timezone.now()
        return max(0, int((self.fin_blocage - maintenant).total_seconds()))

    # -- ecriture -----------------------------------------------------------

    @classmethod
    def enregistrer_echec(cls, email):
        """Incremente le compteur. Repart de 1 si le blocage precedent a
        expire : sans cela, un compte reste bloque a vie apres 5 echecs
        espaces dans le temps."""
        ligne, _ = cls.objects.get_or_create(email=email.lower())
        expire = timezone.now() >= ligne.fin_blocage
        ligne.tentatives = 1 if expire else ligne.tentatives + 1
        ligne.save()
        return ligne

    @classmethod
    def reussite(cls, email):
        """Connexion reussie : le compteur disparait."""
        cls.objects.filter(email=email.lower()).delete()

    @classmethod
    def bloque(cls, email):
        ligne = cls.objects.filter(email=email.lower()).first()
        return ligne is not None and ligne.est_bloque()

    @classmethod
    def comptes_bloques(cls):
        """Lignes actuellement bloquees, appariees a un compte REEL.

        Les adresses inexistantes (fautes de frappe, sondages) sont comptees
        pour le freinage mais n'ont pas a apparaitre dans une liste de comptes.
        """
        maintenant = timezone.now()
        lignes = cls.objects.filter(
            tentatives__gte=cls.MAX_TENTATIVES,
            dernier_echec__gt=maintenant - cls.DUREE_BLOCAGE,
        )
        par_email = {ligne.email: ligne for ligne in lignes}
        if not par_email:
            return []
        utilisateurs = User.objects.filter(email__in=par_email.keys())
        apparies = []
        for utilisateur in utilisateurs:
            ligne = par_email.get(utilisateur.email.lower())
            if ligne is not None:
                apparies.append((utilisateur, ligne))
        return apparies
