import datetime
from decimal import Decimal
import io
import json
import uuid
from math import atan2, cos, radians, sin, sqrt


import qrcode
import qrcode.image.svg
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import IntegrityError, models, transaction
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac

valider_telephone = RegexValidator(
    regex=r'^\+?[0-9 \-]{7,20}$',
    message="Numero de telephone invalide (chiffres, espaces, tirets et + uniquement).",
)


def _qr_svg(donnee, taille_mm=None, box_size=10, border=4):
    """Genere un QR code SVG destine a etre INLINE dans une page HTML.

    `taille_mm` fixe la taille PHYSIQUE voulue : le module est calcule a
    partir du nombre reel de modules du code, qui depend de la longueur de la
    donnee. Un box_size fixe donnerait un code plus grand pour une URL plus
    longue -- et le verso d'une carte n'a pas de place pour ca.

    Pourquoi ce nettoyage : qrcode ecrit ses modules en <svg:rect ...> avec un
    prefixe de namespace. Colle tel quel dans du HTML, c'est invisible -- un
    analyseur HTML ne resout pas les prefixes, il voit un element inconnu
    nomme "svg:rect" et ne dessine rien. Le SVG s'affichait donc comme un
    CARRE BLANC. Constate au rendu navigateur, pas devine.

    On retire donc le prefixe et sa declaration pour obtenir du SVG que le
    parseur HTML comprend. Le SVG n'ayant pas de viewBox, sa taille se regle
    a la generation (box_size / border), jamais en CSS : imposer une largeur
    redimensionne la zone d'affichage sans redimensionner les modules.
    """
    code = qrcode.QRCode(box_size=box_size, border=border,
                         image_factory=qrcode.image.svg.SvgImage)
    code.add_data(donnee)
    code.make(fit=True)
    if taille_mm:
        # SvgImage rend 1 mm par unite de box_size / 10.
        modules = code.modules_count + 2 * border
        code.box_size = max(1, round(taille_mm * 10 / modules))
    buffer = io.BytesIO()
    code.make_image().save(buffer)
    svg = buffer.getvalue().decode("utf-8")
    return (svg.replace('xmlns:svg="http://www.w3.org/2000/svg"', "")
               .replace("<svg:", "<")
               .replace("</svg:", "</"))


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


class Organisme(models.Model):
    """Organisme assureur (IPM, compagnie d'assurance, mutuelle ou entreprise)."""

    class TypeOrganisme(models.TextChoices):
        IPM = "IPM", "Institution de Prévoyance Maladie (IPM)"
        ASSURANCE = "ASSURANCE", "Compagnie d'assurance"
        MUTUELLE = "MUTUELLE", "Mutuelle de santé"
        ENTREPRISE = "ENTREPRISE", "Entreprise"

    CODE_DEFAUT = "IPM-DEFAUT"
    NOM_DEFAUT = "IPM SantéSN Défaut"

    nom = models.CharField("nom de l'organisme", max_length=150)
    code = models.CharField("code unique", max_length=50, unique=True)
    type_organisme = models.CharField(
        "type d'organisme",
        max_length=20,
        choices=TypeOrganisme.choices,
        default=TypeOrganisme.IPM,
    )
    adresse = models.CharField("adresse", max_length=255, blank=True, default="")
    telephone = models.CharField(
        "téléphone", max_length=30, blank=True, default="", validators=[valider_telephone]
    )
    email = models.EmailField("adresse email", blank=True, default="")
    actif = models.BooleanField("organisme actif", default=True)
    date_creation = models.DateTimeField("date de création", auto_now_add=True)

    class Meta:
        verbose_name = "organisme"
        verbose_name_plural = "organismes"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.nom} ({self.code})"

    @classmethod
    def obtenir_defaut(cls):
        """Retourne l'organisme par défaut (en le créant si nécessaire)."""
        organisme, _ = cls.objects.get_or_create(
            code=cls.CODE_DEFAUT,
            defaults={
                "nom": cls.NOM_DEFAUT,
                "type_organisme": cls.TypeOrganisme.IPM,
                "actif": True,
            },
        )
        return organisme


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modèle utilisateur unique de SantéSN.

    Règles métier :
    - authentification par email + mot de passe uniquement
    - le rôle est stocké en base et jamais choisi à la connexion
    - la redirection après connexion dépend du rôle
    """

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrateur Général'
        GESTIONNAIRE = 'GESTIONNAIRE', 'Gestionnaire'
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
    organisme = models.ForeignKey(
        Organisme,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='utilisateurs',
        verbose_name='organisme',
        help_text="Obligatoire pour un compte Gestionnaire.",
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

    def clean(self):
        super().clean()
        if self.role == self.Role.GESTIONNAIRE and not self.organisme_id:
            raise ValidationError(
                {"organisme": "Un gestionnaire doit obligatoirement être rattaché à un organisme."}
            )

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    def get_short_name(self):
        return self.first_name

    # Aides métier utilisées par les décorateurs et les templates
    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def is_gestionnaire(self):
        return self.role == self.Role.GESTIONNAIRE

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

    def est_conventionne_par(self, organisme):
        """Vérifie si le prestataire fait partie du réseau conventionné d'un organisme donné."""
        if not organisme:
            return self.partenaire
        convention = self.conventions_organismes.filter(organisme=organisme).first()
        if convention:
            return convention.statut == ConventionPrestataire.Statut.ACTIF and convention.tiers_payant_actif
        # Si des conventions spécifiques existent pour d'autres organismes, le prestataire n'est pas conventionné par défaut pour celui-ci
        if self.conventions_organismes.exists():
            return False
        return self.partenaire


class ConventionPrestataire(models.Model):
    """
    Rattachement conventionnel d'un établissement de santé (Prestataire)
    auprès d'un organisme assureur (IPM / Compagnie d'assurance / Mutuelle).
    Permet à chaque organisme de gérer son propre réseau conventionné de manière
    strictement indépendante, sans doublonner les comptes des professionnels.
    """
    class Statut(models.TextChoices):
        ACTIF = "ACTIF", "Conventionné actif"
        SUSPENDU = "SUSPENDU", "Convention suspendue"
        EN_ATTENTE = "EN_ATTENTE", "Instruction en cours"
        RESILIE = "RESILIE", "Convention résiliée"

    organisme = models.ForeignKey(
        Organisme,
        on_delete=models.CASCADE,
        related_name="conventions_prestataires",
        verbose_name="organisme assureur",
    )
    prestataire = models.ForeignKey(
        Prestataire,
        on_delete=models.CASCADE,
        related_name="conventions_organismes",
        verbose_name="établissement de soins",
    )
    numero_convention = models.CharField(
        "numéro de convention",
        max_length=60,
        blank=True,
        default="",
        help_text="Référence contractuelle spécifique à cet organisme.",
    )
    statut = models.CharField(
        "statut du conventionnement",
        max_length=20,
        choices=Statut.choices,
        default=Statut.ACTIF,
        db_index=True,
    )
    tiers_payant_actif = models.BooleanField(
        "tiers payant autorisé",
        default=True,
        help_text="Dispense d'avance des frais pour les assurés de cet organisme.",
    )
    date_conventionnement = models.DateField(
        "date d'effet",
        default=timezone.now,
    )
    date_fin = models.DateField(
        "date d'échéance",
        null=True,
        blank=True,
        help_text="Optionnel : date d'échéance ou de renouvellement annuel.",
    )
    remarques = models.CharField(
        "accords / barèmes négociés",
        max_length=255,
        blank=True,
        default="",
    )
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conventions_creees",
        verbose_name="conventionné par",
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "convention prestataire"
        verbose_name_plural = "conventions prestataires"
        constraints = [
            models.UniqueConstraint(
                fields=["organisme", "prestataire"],
                name="convention_unique_organisme_prestataire",
                violation_error_message="Cet établissement possède déjà un dossier de conventionnement auprès de cet organisme.",
            )
        ]
        ordering = ["-date_conventionnement"]

    def __str__(self):
        return f"{self.organisme.nom} ⇄ {self.prestataire.nom} ({self.get_statut_display()})"


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

    class StatutValidation(models.TextChoices):
        VALIDE = "VALIDE", "Validé"
        EN_ATTENTE = "EN_ATTENTE", "En attente de validation"
        REFUSE = "REFUSE", "Refusé"

    type_beneficiaire = models.CharField(
        max_length=20,
        choices=TypeBeneficiaire.choices,
        default=TypeBeneficiaire.PRINCIPAL,
        db_index=True,
    )
    statut_validation = models.CharField(
        "statut de validation IPM",
        max_length=20,
        choices=StatutValidation.choices,
        default=StatutValidation.VALIDE,
        db_index=True,
    )
    document_justificatif = models.FileField(
        "pièce justificative (état civil / scolarité)",
        upload_to="justificatifs_ayants_droit/",
        blank=True,
        null=True,
    )
    date_decision = models.DateTimeField("date de décision", null=True, blank=True)
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ayants_droit_valides",
    )
    motif_refus = models.CharField("motif de refus", max_length=255, blank=True, default="")
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
    organisme = models.ForeignKey(
        Organisme,
        on_delete=models.PROTECT,
        related_name="patients",
        verbose_name="organisme",
        help_text="Organisme (IPM / assureur) de rattachement de l'assuré.",
    )
    entreprise = models.CharField(
        "entreprise",
        max_length=150,
        blank=True,
        default="",
        help_text="Entreprise employeur de l'assuré (optionnel).",
    )

    class Meta:
        ordering = ["nom", "prenom"]

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    def save(self, *args, **kwargs):
        if not self.numero_carte:
            self.numero_carte = self._generer_numero_carte()
        if (
            self.est_ayant_droit
            and self.assure_principal_id
            and self.assure_principal
            and self.assure_principal.organisme_id
        ):
            self.organisme_id = self.assure_principal.organisme_id
        elif not self.organisme_id and self.user_id and getattr(self.user, "organisme_id", None):
            self.organisme_id = self.user.organisme_id
        elif not self.organisme_id:
            self.organisme = Organisme.obtenir_defaut()
        super().save(*args, **kwargs)

    @staticmethod
    def _generer_numero_carte():
        return f"SN-{uuid.uuid4().hex[:10].upper()}"

    def qr_svg(self, url, taille_mm=44):
        """QR (SVG) de la carte de prise en charge, encodant `url`.

        Meme fabrique que Ordonnance.qr_svg -- pas un second systeme.

        Le QR encode une ADRESSE, pas des donnees : scanne, il ouvre une page
        de SantéSN qui exige une connexion et un role autorise. Il ne contient
        aucune donnee medicale, et le numero de carte qu'il porte n'est pas un
        secret (il est deja affiche sur la carte, dans l'espace assure et dans
        les listes) : ce n'est pas lui qui protege, c'est l'authentification.

        L'URL est passee par la vue plutot que construite ici : un modele n'a
        pas de requete, donc pas de nom d'hote.

        TAILLE : elle se regle A LA GENERATION, pas en CSS (voir _qr_svg).
        44 mm par defaut : sur une carte de 85,6 x 54 mm, le code occupe
        l'essentiel du verso en gardant la marge de silence necessaire a une
        lecture fiable. border=2 modules est le minimum recommande.
        """
        return _qr_svg(url, taille_mm=taille_mm, border=2)

    @property
    def est_ayant_droit(self):
        return self.type_beneficiaire == self.TypeBeneficiaire.AYANT_DROIT

    @property
    def est_valide(self):
        """Un assuré principal est toujours valide ; un ayant droit doit être approuvé par l'IPM."""
        if self.type_beneficiaire == self.TypeBeneficiaire.PRINCIPAL:
            return True
        return self.statut_validation == self.StatutValidation.VALIDE

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}".strip()

    @property
    def age(self):
        if not self.date_naissance:
            return None
        aujourdhui = datetime.date.today()
        return (
            aujourdhui.year
            - self.date_naissance.year
            - ((aujourdhui.month, aujourdhui.day) < (self.date_naissance.month, self.date_naissance.day))
        )

    @property
    def titulaire(self):
        """Le beneficiaire porteur du plan de couverture (soi-meme si principal)."""
        return self.assure_principal if self.est_ayant_droit and self.assure_principal_id else self

    @property
    def taux_couverture(self):
        plan = self.titulaire.plan_couverture
        return plan.taux_couverture if plan else None

    def consommation_annuelle_assurance(self, annee=None):
        """Total des remboursements (parts assurance) consommés par le foyer sur l'année civile (consultations + pharmacie + remboursements directs)."""
        from django.apps import apps
        from django.db.models import Sum
        if annee is None:
            annee = timezone.now().year
        titulaire = self.titulaire
        membres_foyer = [titulaire.pk] + list(titulaire.ayants_droit.values_list("pk", flat=True))

        PaiementModel = apps.get_model("Plateform_medicale", "Paiement")
        DelivranceModel = apps.get_model("Plateform_medicale", "Delivrance")
        RemboursementModel = apps.get_model("Plateform_medicale", "DemandeRemboursement")

        total_consultations = PaiementModel.objects.filter(
            consultation__patient_id__in=membres_foyer,
            consultation__date_consultation__year=annee,
        ).aggregate(total=Sum("montant_part_assurance"))["total"] or Decimal("0")

        total_pharmacie = DelivranceModel.objects.filter(
            ordonnance__consultation__patient_id__in=membres_foyer,
            date_delivrance__year=annee,
        ).aggregate(total=Sum("montant_part_assurance"))["total"] or Decimal("0")

        total_remboursements = RemboursementModel.objects.filter(
            patient_id__in=membres_foyer,
            date_soins__year=annee,
            statut__in=["validee", "remboursee"],
        ).aggregate(total=Sum("montant_rembourse_accorde"))["total"] or Decimal("0")

        return total_consultations + total_pharmacie + total_remboursements

    def plafond_annuel_restant(self, annee=None):
        """Montant restant sous le plafond annuel pour l'année civile (None si illimité)."""
        plan = self.titulaire.plan_couverture
        if not plan or plan.plafond_annuel is None or plan.plafond_annuel <= 0:
            return None
        consomme = self.consommation_annuelle_assurance(annee=annee)
        return max(Decimal("0"), Decimal(str(plan.plafond_annuel)) - Decimal(str(consomme)))

    def pourcentage_plafond_consomme(self, annee=None):
        """Pourcentage de consommation du plafond annuel (0.0 si illimité ou nul)."""
        plan = self.titulaire.plan_couverture
        if not plan or plan.plafond_annuel is None or plan.plafond_annuel <= 0:
            return 0.0
        consomme = self.consommation_annuelle_assurance(annee=annee)
        ratio = (Decimal(str(consomme)) / Decimal(str(plan.plafond_annuel))) * 100
        return min(100.0, float(round(ratio, 1)))



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
    presentation = models.TextField(
        "présentation",
        blank=True,
        help_text="Texte libre affiche a l'assure qui choisit son medecin.",
    )
    annees_experience = models.PositiveSmallIntegerField(
        "années d'expérience",
        null=True,
        blank=True,
        help_text="Laisser vide si l'information n'est pas connue.",
    )

    def __str__(self):
        p = self.prenom.strip()
        n = self.nom.strip()
        if p.lower().startswith("dr."):
            p = p[3:].strip()
        elif p.lower().startswith("dr "):
            p = p[3:].strip()
        elif p.lower() == "dr":
            p = ""

        if n.lower().startswith("dr."):
            n = n[3:].strip()
        elif n.lower().startswith("dr "):
            n = n[3:].strip()

        nom_affiche = f"{p} {n}".strip()
        return f"Dr {nom_affiche}" if nom_affiche else "Dr"

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}".strip()


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
        if self.prestataire:
            return f"Pharmacien – {self.prestataire.nom}"
        return "Pharmacien (compte non assigné)"

    @property
    def nom_complet(self):
        if self.user:
            return self.user.get_full_name() or self.user.email
        if self.prestataire:
            return f"Pharmacien – {self.prestataire.nom}"
        return "Pharmacien (compte non assigné)"

    @property
    def email(self):
        if self.user:
            return self.user.email
        return ""


class ServiceMedical(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    prix = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0, message="Le prix ne peut pas être négatif.")],
    )
    prestataire = models.ForeignKey(
        Prestataire,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="services",
    )

    def __str__(self):
        # Inclure le prestataire évite les ambiguïtés quand plusieurs
        # prestataires proposent un service de même nom (ex: "Consultation").
        if self.prestataire_id:
            return f"{self.nom} ({self.prestataire})"
        return self.nom


class PriseEnCharge(models.Model):
    STATUT_CHOICES = [
        ("en_attente", "En attente"),
        ("validee", "Validée"),
        ("refusee", "Refusée"),
        ("terminee", "Terminée"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    date_demande = models.DateTimeField(auto_now_add=True)
    motif = models.TextField("détails ou notes", blank=True, default="")
    numero_pec = models.CharField(
        "numéro de prise en charge",
        max_length=32,
        unique=True,
        blank=True,
        null=True,
        db_index=True,
    )
    montant_estime = models.DecimalField(
        "montant estimé du devis",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Montant estimatif figurant sur le devis remis par la structure de soins.",
    )
    devis_fichier = models.FileField(
        "devis médical (PDF ou scan)",
        upload_to="devis_prises_en_charge/",
        blank=True,
        null=True,
        help_text="Fichier du devis fourni par l'établissement (PDF, JPG, PNG - max 10 Mo).",
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="en_attente",
        db_index=True,
    )
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prises_en_charge_validees",
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    motif_refus = models.CharField("motif de refus", max_length=255, blank=True)

    def save(self, *args, **kwargs):
        if not self.numero_pec:
            self.numero_pec = f"PEC-{uuid.uuid4().hex[:8].upper()}"
        if not self.motif or not self.motif.strip():
            if self.devis_fichier:
                self.motif = "Devis médical numérisé joint"
            else:
                self.motif = "Demande de prise en charge conventionnée"
        super().save(*args, **kwargs)

    @property
    def montant_part_assurance(self):
        if not self.montant_estime:
            return None
        taux = self.patient.taux_couverture
        if not taux:
            return None
        return (self.montant_estime * Decimal(str(taux)) / Decimal("100")).quantize(Decimal("1"))

    @property
    def montant_part_patient(self):
        if not self.montant_estime:
            return None
        part_ass = self.montant_part_assurance
        if part_ass is None:
            return self.montant_estime
        return self.montant_estime - part_ass

    def __str__(self):
        ref = f"[{self.numero_pec}] " if self.numero_pec else ""
        return f"{ref}Prise en charge de {self.patient} - {self.statut}"

    def clean(self):
        """Interdit de changer de patient ou de rétrograder le statut une fois des consultations rattachées."""
        if not self.pk or self.patient_id is None:
            return
        anciennes_valeurs = (
            type(self).objects.filter(pk=self.pk)
            .values("patient_id", "statut")
            .first()
        )
        if anciennes_valeurs:
            patient_enregistre = anciennes_valeurs["patient_id"]
            ancien_statut = anciennes_valeurs["statut"]

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

            # Intégrité financière : interdire la rétrogradation d'une PEC validée
            # vers refusée ou en attente si des consultations / paiements y sont rattachés.
            if (
                ancien_statut == "validee"
                and self.statut in ("refusee", "en_attente")
                and self.consultation_set.exists()
            ):
                raise ValidationError({
                    "statut": (
                        "Cette prise en charge est déjà rattachée à une ou plusieurs "
                        "consultations : son statut ne peut plus être rétrogradé en attente ou refusé."
                    ),
                })


class Consultation(models.Model):
    class TypeAdmission(models.TextChoices):
        RDV = "RDV", "Sur rendez-vous"
        SPONTANE = "SPONTANE", "Passage spontané"
        URGENCE = "URGENCE", "Urgence médicale"

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    medecin = models.ForeignKey(Medecin, on_delete=models.PROTECT)
    service = models.ForeignKey(ServiceMedical, on_delete=models.SET_NULL, null=True, blank=True)
    prise_en_charge = models.ForeignKey(
        PriseEnCharge,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    type_admission = models.CharField(
        "type d'admission",
        max_length=20,
        choices=TypeAdmission.choices,
        default=TypeAdmission.RDV,
        db_index=True,
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
    enregistre_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="paiements_enregistres",
        help_text=(
            "Qui a constate le reglement. Renseigne automatiquement, jamais "
            "saisi. SET_NULL : supprimer un compte n'efface pas l'ecriture."
        ),
    )

    def __str__(self):
        return f"Paiement {self.get_statut_display()} - {self.consultation}"

    @classmethod
    def calculer_pour(cls, consultation):
        """Construit (sans sauvegarder) le Paiement correspondant a une consultation.
        
        Applique le taux de couverture conventionné et plafonne automatiquement
        la part assurance au reliquat budgétaire annuel disponible pour le foyer.
        """
        from django.db.models import Sum
        if hasattr(consultation, "paiement") and consultation.paiement.montant_total and consultation.paiement.montant_total > Decimal("0"):
            montant_total = consultation.paiement.montant_total
        else:
            montant_total = consultation.service.prix if consultation.service_id else Decimal("0")
        taux = Decimal("0")
        prise_en_charge = consultation.prise_en_charge
        if prise_en_charge is not None and prise_en_charge.statut == "validee":
            taux = Decimal(str(consultation.patient.taux_couverture or 0))

        montant_part_assurance = (Decimal(str(montant_total)) * taux / Decimal("100")).quantize(Decimal("0.01"))

        # Application du plafond annuel si présent sur le plan de couverture
        plan = consultation.patient.titulaire.plan_couverture if (consultation.patient_id and consultation.patient.titulaire) else None
        if plan and plan.plafond_annuel is not None and plan.plafond_annuel > 0:
            annee = (consultation.date_consultation or timezone.now()).year
            titulaire = consultation.patient.titulaire
            membres_foyer = [titulaire.pk] + list(titulaire.ayants_droit.values_list("pk", flat=True))
            consomme_deja = Paiement.objects.filter(
                consultation__patient_id__in=membres_foyer,
                consultation__date_consultation__year=annee,
            ).exclude(consultation=consultation).aggregate(total=Sum("montant_part_assurance"))["total"] or Decimal("0")

            reliquat_disponible = max(Decimal("0"), Decimal(str(plan.plafond_annuel)) - Decimal(str(consomme_deja)))
            if montant_part_assurance > reliquat_disponible:
                montant_part_assurance = reliquat_disponible

        montant_part_patient = Decimal(str(montant_total)) - montant_part_assurance
        return cls(
            consultation=consultation,
            montant_total=montant_total,
            taux_applique=taux,
            montant_part_assurance=montant_part_assurance,
            montant_part_patient=montant_part_patient,
        )



class Ordonnance(models.Model):
    class Statut(models.TextChoices):
        ACTIF = "actif", "En attente de délivrance"
        DELIVRE = "delivre", "Délivrée en pharmacie"
        ANNULE = "annule", "Annulée par le médecin"

    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name="ordonnances")
    # CONSERVE VOLONTAIREMENT. Porte le texte des ordonnances anterieures a
    # LigneOrdonnance : il n'est ni transforme ni supprime. blank=True permet
    # aux nouvelles ordonnances de n'avoir que des lignes structurees.
    medicaments = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    code_qr = models.CharField(
        "code de verification",
        max_length=20,
        unique=True,
        editable=False,
        help_text="Encode dans le QR scanne par la pharmacie pour valider l'ordonnance.",
    )
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.ACTIF,
        db_index=True,
    )
    motif_annulation = models.CharField("motif d'annulation", max_length=255, blank=True)
    date_annulation = models.DateTimeField("date d'annulation", null=True, blank=True)
    # Sceau d'integrite (HMAC-SHA256) pose UNE FOIS, a la creation, apres
    # l'enregistrement des lignes. Vide pour les ordonnances anterieures a
    # son introduction : on ne scelle pas retroactivement un contenu dont on
    # ne peut plus garantir qu'il n'a pas deja ete modifie.
    sceau = models.CharField(
        "sceau d'intégrité",
        max_length=64,
        blank=True,
        editable=False,
        help_text="HMAC-SHA256 du contenu de l'ordonnance au moment de la prescription.",
    )

    class Integrite(models.TextChoices):
        INTACTE = "intacte", "Sceau vérifié — contenu intact"
        ALTEREE = "alteree", "Sceau invalide — contenu modifié après prescription"
        NON_SCELLEE = "non_scellee", "Ordonnance antérieure au scellement"

    def __str__(self):
        return f"Ordonnance #{self.code_qr} du {self.date_creation:%d/%m/%Y}"

    @property
    def est_delivree(self):
        return hasattr(self, "delivrance") or self.statut == self.Statut.DELIVRE

    @property
    def est_annulee(self):
        return self.statut == self.Statut.ANNULE

    @property
    def est_expiree(self):
        delai = getattr(settings, "DELAI_VALIDITE_ORDONNANCE_JOURS", 90)
        if not delai:
            return False
        return timezone.now() > (self.date_creation + datetime.timedelta(days=delai))


    def annuler(self, motif=""):
        if hasattr(self, "delivrance") or self.statut == self.Statut.DELIVRE:
            raise ValidationError("Une ordonnance déjà délivrée en pharmacie ne peut plus être annulée.")
        self.statut = self.Statut.ANNULE
        self.motif_annulation = motif
        self.date_annulation = timezone.now()
        self.save(update_fields=["statut", "motif_annulation", "date_annulation"])

    def save(self, *args, **kwargs):
        if not self.code_qr:
            self.code_qr = self._generer_code_qr()
        super().save(*args, **kwargs)

    @staticmethod
    def _generer_code_qr():
        return f"RX-{uuid.uuid4().hex[:10].upper()}"

    # ------------------------------------------------------------------
    # Scellement cryptographique
    # ------------------------------------------------------------------
    # Ce qui est scelle : tout ce qui fait la PRESCRIPTION (qui, pour qui,
    # quand, quoi). Ce qui ne l'est pas : le statut, l'annulation et la
    # delivrance -- ils evoluent legitimement apres la signature.
    #
    # Portee reelle : le sceau detecte toute modification du contenu en base
    # (acces direct a la base, admin, script) apres la prescription. Il ne
    # remplace pas une signature asymetrique verifiable hors ligne : la cle
    # reste sur le serveur.

    _SEL_SCEAU = "santesn.ordonnance.sceau.v1"

    def contenu_canonique(self):
        """Representation deterministe (JSON trie) du contenu scelle."""
        consultation = self.consultation
        lignes = [
            [l.medicament, l.dosage, l.posologie, l.duree, l.quantite]
            for l in self.lignes.order_by("ordre", "pk")
        ]
        donnees = {
            "v": 1,
            "code": self.code_qr,
            "consultation": consultation.pk,
            "patient": consultation.patient_id,
            "medecin": consultation.medecin_id,
            "date": self.date_creation.astimezone(datetime.timezone.utc).isoformat(),
            "lignes": lignes,
            "texte": self.medicaments,
        }
        return json.dumps(donnees, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def calculer_sceau(self):
        cle = getattr(settings, "ORDONNANCE_SCEAU_CLE", "") or None
        return salted_hmac(
            self._SEL_SCEAU, self.contenu_canonique(), secret=cle, algorithm="sha256"
        ).hexdigest()

    def sceller(self):
        """Pose le sceau. A appeler une seule fois, lignes enregistrees."""
        if self.sceau:
            raise ValidationError("Cette ordonnance est déjà scellée.")
        self.sceau = self.calculer_sceau()
        self.save(update_fields=["sceau"])

    def verifier_integrite(self):
        if not self.sceau:
            return self.Integrite.NON_SCELLEE
        if constant_time_compare(self.sceau, self.calculer_sceau()):
            return self.Integrite.INTACTE
        return self.Integrite.ALTEREE

    @property
    def integrite(self):
        return self.verifier_integrite()

    @property
    def sceau_court(self):
        """Empreinte lisible imprimee sur l'ordonnance (16 premiers caracteres)."""
        if not self.sceau:
            return ""
        s = self.sceau[:16].upper()
        return "-".join(s[i:i + 4] for i in range(0, 16, 4))

    @property
    def qr_svg(self):
        """QR code (SVG) encodant le code de verification, scanne par la pharmacie.

        Passe par _qr_svg depuis la correction du prefixe de namespace : le
        code sortait jusqu'ici en CARRE BLANC dans le navigateur, les modules
        n'etant pas dessines. Voir _qr_svg pour le detail.
        """
        return _qr_svg(self.code_qr)



class LigneOrdonnance(models.Model):
    """Une ligne de prescription d'une ordonnance.

    AJOUT PUREMENT ADDITIF. Ordonnance.medicaments (texte libre) n'est ni
    supprime ni transforme : les ordonnances anterieures continuent de
    s'afficher exactement comme avant. Une ordonnance a soit des lignes
    structurees, soit son texte historique -- jamais les deux melanges.

    POURQUOI AUCUN PARSING DES ANCIENNES. Les donnees reelles contiennent au
    moins trois formats, dont des tableaux markdown tapes A LA MAIN par un
    medecin qui a reconstruit la structure manquante. Decouper ce texte
    automatiquement finirait par attribuer un dosage au mauvais medicament,
    sur des ordonnances DEJA DELIVREES. On ne devine pas une prescription.

    POURQUOI PAS DE MODELE Medicament. Aucun referentiel de medicaments
    n'existe dans le projet. En creer un signifierait soit une table vide --
    le medecin ne pourrait rien choisir -- soit la peupler de medicaments
    inventes. `medicament` reste donc du texte ; si un referentiel est acquis
    un jour, une cle etrangere s'ajoutera A COTE, sans rien casser.

    UN SEUL CHAMP OBLIGATOIRE. Une ligne sans medicament n'a pas de sens.
    Imposer en plus une posologie ou une duree pousserait le medecin a
    remplir du vide pour passer la validation : c'est ainsi qu'on fabrique
    de la fausse donnee medicale.
    """

    ordonnance = models.ForeignKey(
        Ordonnance, on_delete=models.CASCADE, related_name="lignes"
    )
    medicament = models.CharField("médicament", max_length=200)
    dosage = models.CharField(max_length=100, blank=True)
    posologie = models.CharField(max_length=200, blank=True)
    duree = models.CharField("durée", max_length=100, blank=True)
    quantite = models.CharField("quantité", max_length=50, blank=True)
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "ligne d'ordonnance"
        verbose_name_plural = "lignes d'ordonnance"
        # pk en second : deux lignes saisies avec le meme ordre gardent
        # malgre tout leur ordre de creation, jamais un ordre aleatoire.
        ordering = ["ordre", "pk"]

    def __str__(self):
        return f"{self.medicament} {self.dosage}".strip()


class RendezVous(models.Model):
    """Rendez-vous d'un patient avec un medecin, aupres d'un prestataire."""

    class Statut(models.TextChoices):
        DEMANDE = "DEMANDE", "Demande"
        CONFIRME = "CONFIRME", "Confirmé"
        REFUSE = "REFUSE", "Refusé"
        ANNULE = "ANNULE", "Annulé"
        ABSENT = "ABSENT", "Absent (non venu)"
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
    motif = models.TextField(
        "motif / symptômes",
        blank=True,
        help_text=(
            "Decrit par le PATIENT lors de sa demande. Ce n'est pas un "
            "diagnostic : le diagnostic appartient au medecin et vit dans "
            "Consultation.diagnostic."
        ),
    )
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
        constraints = [
            # Un medecin ne peut pas etre a deux endroits a la fois. Sans
            # cette contrainte, deux patients pouvaient reserver le MEME
            # creneau chez le MEME medecin -- le systeme acceptait, et les
            # deux se presentaient.
            #
            # Les rendez-vous ANNULES, REFUSES et ABSENTS sont exclus : annuler, refuser
            # ou constater l'absence libere le creneau pour un autre patient.
            models.UniqueConstraint(
                fields=["medecin", "date_heure"],
                condition=~models.Q(statut__in=["ANNULE", "REFUSE", "ABSENT"]),
                name="rdv_creneau_unique_par_medecin",
                violation_error_message=(
                    "Ce créneau est déjà réservé pour ce médecin. "
                    "Choisissez une autre date ou une autre heure."
                ),
            ),
        ]

    def clean(self):
        """Message lisible avant que la contrainte de base ne parle.

        La contrainte ci-dessus est le filet de securite ; elle produit une
        erreur globale. Ici on rattache le probleme au champ que
        l'utilisateur doit corriger : la date et l'heure.
        """
        super().clean()
        if self.medecin_id is None or self.date_heure is None:
            return
        if self.statut in (self.Statut.ANNULE, self.Statut.REFUSE, self.Statut.ABSENT):
            return
        conflit = RendezVous.objects.filter(
            medecin_id=self.medecin_id, date_heure=self.date_heure
        ).exclude(statut__in=[self.Statut.ANNULE, self.Statut.REFUSE, self.Statut.ABSENT])
        if self.pk:
            conflit = conflit.exclude(pk=self.pk)
        if conflit.exists():
            raise ValidationError({
                "date_heure": (
                    "Ce créneau est déjà réservé pour ce médecin. "
                    "Choisissez une autre date ou une autre heure."
                ),
            })

    def __str__(self):
        return f"RDV {self.patient} - {self.medecin} ({self.date_heure:%d/%m/%Y %H:%M})"


class Delivrance(models.Model):
    """Delivrance d'une ordonnance par un pharmacien (une seule par ordonnance)."""

    ordonnance = models.OneToOneField(Ordonnance, on_delete=models.CASCADE, related_name="delivrance")
    pharmacien = models.ForeignKey(Pharmacien, on_delete=models.PROTECT, related_name="delivrances")
    date_delivrance = models.DateTimeField(auto_now_add=True)

    montant_total = models.DecimalField(
        "Montant total des médicaments (FCFA)",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    taux_couverture = models.DecimalField(
        "Taux de prise en charge appliqué (%)",
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))],
    )
    montant_part_assurance = models.DecimalField(
        "Part prise en charge / IPM (FCFA)",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    montant_part_patient = models.DecimalField(
        "Part payée par le patient / Ticket modérateur (FCFA)",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        verbose_name = "delivrance"
        verbose_name_plural = "delivrances"
        ordering = ["-date_delivrance"]

    def __str__(self):
        return f"Delivrance de {self.ordonnance} par {self.pharmacien}"

    def calculer_partages(self):
        """Calcule la part assurance et le ticket modérateur selon le montant total et le taux de couverture."""
        total = self.montant_total or Decimal("0.00")
        taux = self.taux_couverture or Decimal("0.00")
        if total > Decimal("0.00") and taux > Decimal("0.00"):
            self.montant_part_assurance = (total * taux / Decimal("100")).quantize(Decimal("1"))
            self.montant_part_patient = total - self.montant_part_assurance
        else:
            self.montant_part_assurance = Decimal("0.00")
            self.montant_part_patient = total


class Notification(models.Model):
    """Notification d'événement système ou métier à destination d'un utilisateur."""

    class TypeEvenement(models.TextChoices):
        RDV_DEMANDE = "RDV_DEMANDE", "Demande de rendez-vous"
        RDV_CONFIRME = "RDV_CONFIRME", "Rendez-vous confirmé"
        RDV_REFUSE = "RDV_REFUSE", "Rendez-vous refusé"
        RDV_ANNULE = "RDV_ANNULE", "Rendez-vous annulé"
        PEC_DEMANDE = "PEC_DEMANDE", "Demande de prise en charge"
        PEC_VALIDEE = "PEC_VALIDEE", "Prise en charge validée"
        PEC_REFUSEE = "PEC_REFUSEE", "Prise en charge refusée"
        ORDONNANCE_CREEE = "ORDONNANCE_CREEE", "Nouvelle ordonnance"
        DELIVRANCE_EFFECTUEE = "DELIVRANCE_EFFECTUEE", "Délivrance effectuée"
        SUPPORT_DEMANDE = "SUPPORT_DEMANDE", "Nouvelle demande d'assistance"
        SUPPORT_REPONSE = "SUPPORT_REPONSE", "Réponse de l'administration"
        AYANT_DROIT_SOUMIS = "AYANT_DROIT_SOUMIS", "Demande d'ayant droit soumise"
        AYANT_DROIT_VALIDE = "AYANT_DROIT_VALIDE", "Ayant droit validé par l'IPM"
        AYANT_DROIT_REFUSE = "AYANT_DROIT_REFUSE", "Ayant droit refusé par l'IPM"
        SYSTEME = "SYSTEME", "Notification système"

    destinataire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    titre = models.CharField(max_length=200, default="Notification")
    message = models.TextField()
    type_evenement = models.CharField(
        max_length=30, choices=TypeEvenement.choices, default=TypeEvenement.SYSTEME
    )
    url_action = models.CharField(max_length=500, blank=True)
    lue = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    email_envoye = models.BooleanField(default=False)
    email_erreur = models.TextField(blank=True)

    class Meta:
        verbose_name = "notification"
        verbose_name_plural = "notifications"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.titre} pour {self.destinataire} ({self.date_creation:%d/%m/%Y})"


class PreferenceNotification(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferences_notifications",
    )
    email_rdv = models.BooleanField(default=True)
    email_prise_en_charge = models.BooleanField(default=True)
    email_ordonnance = models.BooleanField(default=True)
    email_delivrance = models.BooleanField(default=True)

    def __str__(self):
        return f"Préférences notifications de {self.user}"


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
        email_norm = email.lower()
        with transaction.atomic():
            ligne = cls.objects.select_for_update().filter(email=email_norm).first()
            if ligne is None:
                try:
                    with transaction.atomic():
                        ligne = cls.objects.create(email=email_norm, tentatives=1)
                        return ligne
                except IntegrityError:
                    ligne = cls.objects.select_for_update().get(email=email_norm)
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


class JournalActivite(models.Model):
    """Trace des DECISIONS administratives et des DESTRUCTIONS.

    Perimetre volontairement etroit. Ne sont PAS journalises :
      - les connexions et la navigation (bruit ; le blocage temporaire a deja
        son propre ecran, cf. TentativeConnexion) ;
      - les actes de soin (une Consultation porte deja son medecin et sa date,
        une Delivrance son pharmacien) -- les reecrire ici les dupliquerait
        sans rien apprendre ;
      - le changement de statut d'un rendez-vous : c'est le travail quotidien
        du medecin, son volume noierait les entrees qui comptent ;
      - les creations metier courantes (service, prestataire...) : la fiche
        creee EST la trace. On journalise la disparition d'un objet, pas sa
        naissance -- sauf pour un compte, car creer un compte accorde un
        acces, ce qui est une decision de securite.

    POINT CENTRAL : l'objet concerne est decrit par du TEXTE FIGE, jamais par
    une cle etrangere. Une cle etrangere en CASCADE effacerait l'entree en
    meme temps que l'objet supprime -- or c'est precisement la suppression
    qu'on veut garder. Meme raison pour auteur_libelle, fige a cote de la cle
    auteur : supprimer le compte d'un administrateur ne doit pas effacer la
    trace de ce qu'il a fait.
    """

    class Action(models.TextChoices):
        CREATION = "CREATION", "Création"
        MODIFICATION = "MODIFICATION", "Modification"
        SUPPRESSION = "SUPPRESSION", "Suppression"
        ACTIVATION = "ACTIVATION", "Activation"
        DESACTIVATION = "DESACTIVATION", "Désactivation"
        DEBLOCAGE = "DEBLOCAGE", "Déblocage"
        MOT_DE_PASSE = "MOT_DE_PASSE", "Mot de passe réinitialisé"
        DECISION = "DECISION", "Décision"
        REGLEMENT = "REGLEMENT", "Règlement"
        IMPORT = "IMPORT", "Import en masse"
        # Editer une carte, c'est delivrer une piece d'identite de couverture :
        # on trace QUI l'a editee et POUR QUI. Le serveur ne peut pas observer
        # la boite de dialogue d'impression du navigateur -- ce qu'on
        # enregistre est donc l'edition, pas l'impression elle-meme.
        CARTE = "CARTE", "Carte éditée"
        # Ordonnance dont le sceau ne correspond plus au contenu : c'est une
        # alerte de securite (falsification probable), pas un acte de soin.
        INTEGRITE = "INTEGRITE", "Alerte d'intégrité"
        # Traçabilité légale d'accès au Dossier Patient Informatisé (Loi 2008-12 CDP Sénégal)
        ACCES_DPI = "ACCES_DPI", "Accès dossier patient"

    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actions_journalisees",
    )
    auteur_libelle = models.CharField("auteur (figé)", max_length=254)
    organisme = models.ForeignKey(
        Organisme,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="journaux",
        verbose_name="organisme",
    )
    organisme_libelle = models.CharField(
        "organisme (figé)", max_length=200, blank=True, default=""
    )
    action = models.CharField(max_length=20, choices=Action.choices, db_index=True)
    objet = models.CharField("objet concerné", max_length=200)
    details = models.CharField("détail", max_length=300, blank=True)
    date = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "entrée du journal"
        verbose_name_plural = "journal d'activité"
        ordering = ["-date"]

    def save(self, *args, **kwargs):
        if self.organisme_id and not self.organisme_libelle and self.organisme:
            self.organisme_libelle = str(self.organisme)
        super().save(*args, **kwargs)

    def __str__(self):
        return (f"{self.date:%d/%m/%Y %H:%M} · {self.auteur_libelle} · "
                f"{self.get_action_display()} · {self.objet}")


class DemandeSupport(models.Model):
    """Demande d'assistance transmise par un assuré à l'administration SantéSN."""

    class Categorie(models.TextChoices):
        RENDEZ_VOUS = "RDV", "Rendez-vous"
        PRISE_EN_CHARGE = "PEC", "Prise en charge & Remboursement"
        ORDONNANCE = "ORDONNANCE", "Ordonnance & Pharmacie"
        COMPTE = "COMPTE", "Carte d'assuré & Données du compte"
        AYANT_DROIT = "AYANT_DROIT", "Ayants droit & Famille"
        TECHNIQUE = "TECHNIQUE", "Problème technique"
        AUTRE = "AUTRE", "Autre demande"

    class Priorite(models.TextChoices):
        BASSE = "BASSE", "Basse"
        NORMALE = "NORMALE", "Normale"
        URGENTE = "URGENTE", "Urgente"

    class Statut(models.TextChoices):
        EN_ATTENTE = "EN_ATTENTE", "En attente"
        EN_COURS = "EN_COURS", "En cours"
        REPONDU = "REPONDU", "Réponse envoyée"
        FERME = "FERME", "Clôturée"

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="demandes_support",
        null=True,
        blank=True,
    )
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="demandes_support",
    )
    numero_dossier = models.CharField(max_length=20, unique=True, editable=False)
    objet = models.CharField(max_length=150)
    categorie = models.CharField(
        max_length=20,
        choices=Categorie.choices,
        default=Categorie.AUTRE,
        db_index=True,
    )
    priorite = models.CharField(
        max_length=20,
        choices=Priorite.choices,
        default=Priorite.NORMALE,
        db_index=True,
    )
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE,
        db_index=True,
    )
    date_creation = models.DateTimeField(auto_now_add=True, db_index=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)
    cloture_le = models.DateTimeField(null=True, blank=True)
    cloture_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        verbose_name = "demande de support"
        verbose_name_plural = "demandes de support"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.numero_dossier} · {self.objet} ({self.get_statut_display()})"

    def save(self, *args, **kwargs):
        if not self.numero_dossier:
            self.numero_dossier = f"SUP-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class MessageSupport(models.Model):
    """Message échangé dans le fil d'une demande d'assistance (patient ou administration)."""

    demande = models.ForeignKey(
        DemandeSupport,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages_support",
    )
    message = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "message de support"
        verbose_name_plural = "messages de support"
        ordering = ["date_envoi"]

    def __str__(self):
        return f"Message de {self.auteur} sur {self.demande.numero_dossier} ({self.date_envoi:%d/%m/%Y %H:%M})"


class FichierMedia(models.Model):
    """Stockage persistant en base de données pour les fichiers médias (documents justificatifs, etc.).
    Permet la persistance intégrale des fichiers sur architecture serverless (Vercel) sans perte de données.
    """
    chemin = models.CharField(max_length=255, unique=True, db_index=True)
    contenu = models.BinaryField()
    type_mime = models.CharField(max_length=120, default="application/octet-stream")
    taille = models.PositiveIntegerField(default=0)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "fichier média persistant"
        verbose_name_plural = "fichiers médias persistants"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.chemin} ({self.taille} octets)"


class DemandeRemboursement(models.Model):
    """
    Demande de remboursement soumise par un assuré ayant consulté ou acheté des
    médicaments auprès d'un établissement HORS RÉSEAU (non conventionné avec son
    organisme / entreprise). L'assuré avance les frais et transmet la facture
    acquittée pour instruction et remboursement par le gestionnaire de son IPM.
    """

    class TypeSoin(models.TextChoices):
        CONSULTATION = "CONSULTATION", "Consultation médicale"
        PHARMACIE = "PHARMACIE", "Pharmacie / Médicaments"
        BIOLOGIE = "BIOLOGIE", "Analyses / Laboratoire"
        IMAGERIE = "IMAGERIE", "Radiologie / Imagerie"
        DENTAIRE = "DENTAIRE", "Soins dentaires"
        OPTIQUE = "OPTIQUE", "Optique / Lunetterie"
        HOSPITALISATION = "HOSPITALISATION", "Hospitalisation"
        AUTRE = "AUTRE", "Autre acte médical"

    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente d'instruction"
        VALIDEE = "validee", "Validée (en cours de règlement)"
        REMBOURSEE = "remboursee", "Remboursée"
        REFUSEE = "refusee", "Refusée"

    class ModeRemboursement(models.TextChoices):
        VIREMENT = "VIREMENT", "Virement bancaire"
        MOBILE_MONEY = "MOBILE_MONEY", "Mobile Money (Wave / Orange Money)"
        CHEQUE = "CHEQUE", "Chèque"
        ESPECES = "ESPECES", "Espèces / Guichet"

    numero_dossier = models.CharField(
        "numéro de dossier",
        max_length=32,
        unique=True,
        editable=False,
        db_index=True,
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="demandes_remboursement",
        verbose_name="bénéficiaire des soins",
    )
    organisme = models.ForeignKey(
        Organisme,
        on_delete=models.PROTECT,
        related_name="demandes_remboursement",
        verbose_name="organisme assureur",
    )
    prestataire_nom = models.CharField(
        "établissement / praticien hors réseau",
        max_length=150,
        help_text="Nom de la clinique, du cabinet ou de la pharmacie où les soins ont été réglés.",
    )
    prestataire = models.ForeignKey(
        Prestataire,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="demandes_remboursement",
        verbose_name="prestataire répertorié (optionnel)",
    )
    type_soin = models.CharField(
        "nature des soins",
        max_length=25,
        choices=TypeSoin.choices,
        default=TypeSoin.CONSULTATION,
        db_index=True,
    )
    date_soins = models.DateField("date des soins")
    montant_depense = models.DecimalField(
        "montant payé par l'assuré (FCFA)",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("1"), message="Le montant dépensé doit être strictement positif.")],
    )
    taux_applique = models.DecimalField(
        "taux de couverture (%)",
        max_digits=5,
        decimal_places=2,
        default=Decimal("0"),
    )
    montant_rembourse_estime = models.DecimalField(
        "montant remboursable estimé (FCFA)",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
    )
    montant_rembourse_accorde = models.DecimalField(
        "montant accordé par l'organisme (FCFA)",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
    )
    justificatif = models.FileField(
        "facture acquittée / feuille de soins",
        upload_to="justificatifs_remboursements/",
        blank=True,
        null=True,
        help_text="Facture acquittée, ticket de caisse ou feuille de soins (PDF, JPG, PNG - max 10 Mo).",
    )
    motif = models.TextField("détails ou observations", blank=True, default="")
    coordonnees_remboursement = models.CharField(
        "numéro Mobile Money ou IBAN souhaité",
        max_length=120,
        blank=True,
        default="",
        help_text="Optionnel : numéro Wave / Orange Money ou IBAN pour recevoir le remboursement.",
    )
    statut = models.CharField(
        "statut",
        max_length=20,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE,
        db_index=True,
    )
    mode_remboursement = models.CharField(
        "mode de règlement",
        max_length=25,
        choices=ModeRemboursement.choices,
        blank=True,
        default="",
    )
    reference_reglement = models.CharField(
        "référence de virement / transaction",
        max_length=100,
        blank=True,
        default="",
    )
    date_demande = models.DateTimeField("date de soumission", auto_now_add=True, db_index=True)
    date_decision = models.DateTimeField("date d'instruction", null=True, blank=True)
    date_reglement = models.DateTimeField("date de remboursement effectif", null=True, blank=True)
    traite_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="remboursements_instruits",
        verbose_name="instruit par",
    )
    motif_refus = models.CharField("motif du refus", max_length=255, blank=True, default="")

    class Meta:
        verbose_name = "demande de remboursement"
        verbose_name_plural = "demandes de remboursement"
        ordering = ["-date_demande"]

    def __str__(self):
        return f"[{self.numero_dossier}] Remboursement {self.patient} - {self.prestataire_nom} ({self.get_statut_display()})"

    def calculer_estimation(self):
        """Calcule (taux, montant_remboursable) selon le plan de couverture et le plafond annuel restant."""
        if not self.patient_id or not self.montant_depense:
            return Decimal("0"), Decimal("0")
        taux = Decimal(str(self.patient.taux_couverture or 0))
        montant_brut = (Decimal(str(self.montant_depense)) * taux / Decimal("100")).quantize(Decimal("0.01"))

        plan = self.patient.titulaire.plan_couverture if self.patient.titulaire else None
        if plan and plan.plafond_annuel is not None and plan.plafond_annuel > 0:
            annee = self.date_soins.year if self.date_soins else timezone.now().year
            from django.db.models import Sum
            titulaire = self.patient.titulaire
            membres_foyer = [titulaire.pk] + list(titulaire.ayants_droit.values_list("pk", flat=True))
            consomme_consult = Paiement.objects.filter(
                consultation__patient_id__in=membres_foyer,
                consultation__date_consultation__year=annee,
            ).aggregate(total=Sum("montant_part_assurance"))["total"] or Decimal("0")
            consomme_pharma = Delivrance.objects.filter(
                ordonnance__consultation__patient_id__in=membres_foyer,
                date_delivrance__year=annee,
            ).aggregate(total=Sum("montant_part_assurance"))["total"] or Decimal("0")
            consomme_remb = DemandeRemboursement.objects.filter(
                patient_id__in=membres_foyer,
                date_soins__year=annee,
                statut__in=[self.Statut.VALIDEE, self.Statut.REMBOURSEE],
            ).exclude(pk=self.pk).aggregate(total=Sum("montant_rembourse_accorde"))["total"] or Decimal("0")
            deja_consomme = consomme_consult + consomme_pharma + consomme_remb
            reliquat = max(Decimal("0"), Decimal(str(plan.plafond_annuel)) - deja_consomme)
            if montant_brut > reliquat:
                montant_brut = reliquat

        return taux, montant_brut

    @property
    def reste_a_charge(self):
        montant_ref = self.montant_rembourse_accorde if self.statut in (self.Statut.VALIDEE, self.Statut.REMBOURSEE) else self.montant_rembourse_estime
        return max(Decimal("0"), (self.montant_depense or Decimal("0")) - (montant_ref or Decimal("0")))

    def clean(self):
        super().clean()
        if self.date_soins and self.date_soins > timezone.now().date():
            raise ValidationError({"date_soins": "La date des soins ne peut pas être dans le futur."})

    def save(self, *args, **kwargs):
        if not self.numero_dossier:
            self.numero_dossier = f"RMB-{uuid.uuid4().hex[:8].upper()}"
        if not self.organisme_id and self.patient_id and self.patient.organisme_id:
            self.organisme_id = self.patient.organisme_id
        elif not self.organisme_id:
            self.organisme = Organisme.obtenir_defaut()
        if self.prestataire_id and not self.prestataire_nom:
            self.prestataire_nom = self.prestataire.nom
        if self.patient_id and self.montant_depense and self.statut == self.Statut.EN_ATTENTE:
            taux, estime = self.calculer_estimation()
            self.taux_applique = taux
            self.montant_rembourse_estime = estime
        super().save(*args, **kwargs)

