from django.db import models


class Patient(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    telephone = models.CharField(max_length=20)
    adresse = models.TextField(blank=True)

    def __str__(self):
        return f"{self.prenom} {self.nom}"


class Medecin(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    specialite = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"Dr {self.prenom} {self.nom}"


class ServiceMedical(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.nom


class PriseEnCharge(models.Model):
    STATUT_CHOICES = [
        ("en_attente", "En attente"),
        ("validee", "Validee"),
        ("refusee", "Refusee"),
        ("terminee", "Terminee"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    date_demande = models.DateTimeField(auto_now_add=True)
    motif = models.TextField()
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="en_attente",
    )

    def __str__(self):
        return f"Prise en charge de {self.patient} - {self.statut}"


class Consultation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)
    service = models.ForeignKey(ServiceMedical, on_delete=models.SET_NULL, null=True)
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


class Ordonnance(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    medicaments = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ordonnance du {self.date_creation:%d/%m/%Y}"
