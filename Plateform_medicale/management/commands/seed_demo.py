import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from Plateform_medicale.models import (
    User, PlanCouverture, Prestataire, Patient, Medecin,
    Pharmacien, ServiceMedical, PriseEnCharge, Consultation,
    Paiement, Ordonnance, LigneOrdonnance, RendezVous
)

class Command(BaseCommand):
    help = "Initialise automatiquement les comptes et donnees de demonstration pour le deploiement."

    def handle(self, *args, **options):
        self.stdout.write("Initialisation des donnees de demonstration SanteSN...")

        # 1. Comptes Utilisateurs
        admin, _ = User.objects.get_or_create(
            email="admin@santesn.sn",
            defaults={"first_name": "Admin", "last_name": "IPM", "role": User.Role.ADMIN, "is_staff": True}
        )
        admin.set_password("Password123")
        admin.is_active = True
        admin.save()

        medecin_user, _ = User.objects.get_or_create(
            email="medecin@santesn.sn",
            defaults={"first_name": "Ibrahima", "last_name": "Ndiaye", "role": User.Role.MEDECIN, "phone_number": "772345678"}
        )
        medecin_user.set_password("Password123")
        medecin_user.is_active = True
        medecin_user.save()

        pharma_user, _ = User.objects.get_or_create(
            email="pharmacien@santesn.sn",
            defaults={"first_name": "Awa", "last_name": "Sow", "role": User.Role.PHARMACIEN, "phone_number": "773456789"}
        )
        pharma_user.set_password("Password123")
        pharma_user.is_active = True
        pharma_user.save()

        assure_user, _ = User.objects.get_or_create(
            email="assure@santesn.sn",
            defaults={"first_name": "Moussa", "last_name": "Diop", "role": User.Role.ASSURE, "phone_number": "771234567"}
        )
        assure_user.set_password("Password123")
        assure_user.is_active = True
        assure_user.save()

        # 2. Plans de couverture
        plan_standard, _ = PlanCouverture.objects.get_or_create(
            nom="Plan Standard IPM (80%)",
            defaults={"taux_couverture": Decimal("80.00"), "plafond_annuel": Decimal("1000000.00")}
        )
        plan_premium, _ = PlanCouverture.objects.get_or_create(
            nom="Plan Cadre Supérieur (90%)",
            defaults={"taux_couverture": Decimal("90.00"), "plafond_annuel": Decimal("2500000.00")}
        )

        # 3. Prestataires
        hopital, _ = Prestataire.objects.get_or_create(
            nom="Hôpital Principal de Dakar",
            defaults={"type_prestataire": Prestataire.Type.HOPITAL, "ville": "Dakar", "adresse": "1 Avenue Nelson Mandela, Dakar", "telephone": "338395050", "latitude": 14.6644, "longitude": -17.4332}
        )
        pharma, _ = Prestataire.objects.get_or_create(
            nom="Grande Pharmacie Dakaroise",
            defaults={"type_prestataire": Prestataire.Type.PHARMACIE, "ville": "Dakar", "adresse": "Boulevard de la République, Dakar", "telephone": "338212121", "latitude": 14.6710, "longitude": -17.4350}
        )

        # 4. Profils Métier
        medecin, _ = Medecin.objects.get_or_create(
            user=medecin_user,
            defaults={"nom": "Ndiaye", "prenom": "Ibrahima", "specialite": "Médecine Générale", "telephone": "772345678", "email": "medecin@santesn.sn", "prestataire": hopital}
        )

        pharmacien, _ = Pharmacien.objects.get_or_create(
            user=pharma_user,
            defaults={"nom": "Grande Pharmacie Dakaroise", "prestataire": pharma}
        )

        patient, _ = Patient.objects.get_or_create(
            user=assure_user,
            defaults={"nom": "Diop", "prenom": "Moussa", "date_naissance": datetime.date(1988, 6, 15), "telephone": "771234567", "adresse": "Mermoz Pyrotechnie, Dakar", "plan_couverture": plan_standard, "type_beneficiaire": Patient.TypeBeneficiaire.PRINCIPAL}
        )

        # Ayant droit
        ayant_droit, _ = Patient.objects.get_or_create(
            nom="Diop", prenom="Aminata",
            defaults={"date_naissance": datetime.date(2018, 3, 22), "type_beneficiaire": Patient.TypeBeneficiaire.AYANT_DROIT, "assure_principal": patient, "lien_parente": Patient.LienParente.ENFANT, "plan_couverture": plan_standard}
        )

        # 5. Service Médical
        service, _ = ServiceMedical.objects.get_or_create(
            nom="Consultation Médecine Générale",
            defaults={"code": "CS-GEN", "prix": Decimal("15000.00"), "taux_remboursement": Decimal("80.00"), "prestataire": hopital}
        )

        # 6. Consultation & Ordonnance de démonstration
        pec, _ = PriseEnCharge.objects.get_or_create(
            patient=patient,
            motif="Consultation de routine et suivi tensionnel",
            defaults={"statut": "validee"}
        )

        consultation, _ = Consultation.objects.get_or_create(
            patient=patient,
            medecin=medecin,
            defaults={"service": service, "prise_en_charge": pec, "date_consultation": timezone.now(), "diagnostic": "Bilan de santé régulier et surveillance de la tension artérielle."}
        )

        paiement, _ = Paiement.objects.get_or_create(
            consultation=consultation,
            defaults={"montant_total": Decimal("15000.00"), "taux_applique": Decimal("80.00"), "montant_part_assurance": Decimal("12000.00"), "montant_part_patient": Decimal("3000.00"), "statut": Paiement.Statut.REGLE, "mode_reglement": Paiement.ModeReglement.ESPECES}
        )

        ordonnance, _ = Ordonnance.objects.get_or_create(
            consultation=consultation,
            defaults={"statut": Ordonnance.Statut.ACTIF}
        )

        if not ordonnance.lignes.exists():
            LigneOrdonnance.objects.create(ordonnance=ordonnance, medicament="Paracétamol 1g", posologie="1 comprimé 3 fois par jour", duree="5 jours", quantite="1 boîte")
            LigneOrdonnance.objects.create(ordonnance=ordonnance, medicament="Amoxicilline 500mg", posologie="1 gélule matin et soir", duree="7 jours", quantite="2 boîtes")

        self.stdout.write(self.style.SUCCESS("[OK] Donnees de demonstration initialisees avec succes !"))
