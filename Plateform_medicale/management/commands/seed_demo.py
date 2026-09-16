import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from Plateform_medicale.models import (
    Consultation,
    LigneOrdonnance,
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


class Command(BaseCommand):
    help = "Initialise ou réinitialise de façon idempotente les 4 comptes et données de démonstration SantéSN."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            type=str,
            default="Passer123!",
            help="Mot de passe unifié pour les 4 comptes de démonstration (par défaut: Passer123!).",
        )

    def handle(self, *args, **options):
        mot_de_passe = options["password"]
        self.stdout.write("Initialisation des données de démonstration SantéSN...")

        # 1. Comptes Utilisateurs pour chaque rôle
        comptes_specs = [
            {
                "email": "admin@santesn.sn",
                "first_name": "Administrateur",
                "last_name": "SantéSN",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "phone_number": "770000001",
            },
            {
                "email": "medecin@santesn.sn",
                "first_name": "Ibrahima",
                "last_name": "Ndiaye",
                "role": User.Role.MEDECIN,
                "is_staff": False,
                "phone_number": "772345678",
            },
            {
                "email": "pharmacien@santesn.sn",
                "first_name": "Awa",
                "last_name": "Sow",
                "role": User.Role.PHARMACIEN,
                "is_staff": False,
                "phone_number": "773456789",
            },
            {
                "email": "assure@santesn.sn",
                "first_name": "Moussa",
                "last_name": "Diop",
                "role": User.Role.ASSURE,
                "is_staff": False,
                "phone_number": "771234567",
            },
        ]

        utilisateurs = {}
        for spec in comptes_specs:
            user, cree = User.objects.get_or_create(
                email=spec["email"],
                defaults={
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                    "role": spec["role"],
                    "is_staff": spec["is_staff"],
                    "phone_number": spec["phone_number"],
                },
            )
            # Garantit le rôle, l'activation et le mot de passe
            user.role = spec["role"]
            user.is_staff = spec["is_staff"]
            user.is_active = True
            user.set_password(mot_de_passe)
            user.save()
            utilisateurs[spec["role"]] = user
            statut_txt = "créé" if cree else "mis à jour"
            self.stdout.write(f"  [Compte] {spec['email']} ({spec['role']}) -> {statut_txt}")

        # 2. Plans de couverture
        plan_standard, _ = PlanCouverture.objects.get_or_create(
            nom="Plan Standard IPM (80%)",
            defaults={
                "taux_couverture": Decimal("80.00"),
                "plafond_annuel": Decimal("1000000.00"),
            },
        )
        plan_premium, _ = PlanCouverture.objects.get_or_create(
            nom="Plan Cadre Supérieur (90%)",
            defaults={
                "taux_couverture": Decimal("90.00"),
                "plafond_annuel": Decimal("2500000.00"),
            },
        )

        # 3. Prestataires partenaires
        hopital, _ = Prestataire.objects.get_or_create(
            nom="Hôpital Principal de Dakar",
            defaults={
                "type_prestataire": Prestataire.Type.HOPITAL,
                "ville": "Dakar",
                "adresse": "1 Avenue Nelson Mandela, Dakar Plateau",
                "telephone": "338395050",
                "partenaire": True,
                "latitude": Decimal("14.6644"),
                "longitude": Decimal("-17.4332"),
            },
        )
        if not hopital.partenaire:
            hopital.partenaire = True
            hopital.save(update_fields=["partenaire"])

        pharmacie, _ = Prestataire.objects.get_or_create(
            nom="Grande Pharmacie Dakaroise",
            defaults={
                "type_prestataire": Prestataire.Type.PHARMACIE,
                "ville": "Dakar",
                "adresse": "Boulevard de la République, Dakar",
                "telephone": "338212121",
                "partenaire": True,
                "latitude": Decimal("14.6710"),
                "longitude": Decimal("-17.4350"),
            },
        )
        if not pharmacie.partenaire:
            pharmacie.partenaire = True
            pharmacie.save(update_fields=["partenaire"])

        # 4. Profils métier rattachés aux utilisateurs
        medecin_user = utilisateurs[User.Role.MEDECIN]
        medecin, _ = Medecin.objects.get_or_create(
            user=medecin_user,
            defaults={
                "nom": medecin_user.last_name,
                "prenom": medecin_user.first_name,
                "specialite": "Médecine Générale",
                "telephone": medecin_user.phone_number or "772345678",
                "email": medecin_user.email,
                "prestataire": hopital,
                "annees_experience": 12,
                "presentation": "Médecin généraliste référent, conventionné IPM SantéSN.",
            },
        )
        if medecin.prestataire_id != hopital.pk:
            medecin.prestataire = hopital
            medecin.save(update_fields=["prestataire"])

        pharma_user = utilisateurs[User.Role.PHARMACIEN]
        pharmacien, _ = Pharmacien.objects.get_or_create(
            user=pharma_user,
            defaults={"prestataire": pharmacie},
        )
        if pharmacien.prestataire_id != pharmacie.pk:
            pharmacien.prestataire = pharmacie
            pharmacien.save(update_fields=["prestataire"])

        assure_user = utilisateurs[User.Role.ASSURE]
        patient, _ = Patient.objects.get_or_create(
            user=assure_user,
            defaults={
                "nom": assure_user.last_name,
                "prenom": assure_user.first_name,
                "date_naissance": datetime.date(1988, 6, 15),
                "telephone": assure_user.phone_number or "771234567",
                "adresse": "Mermoz Pyrotechnie, Dakar",
                "plan_couverture": plan_standard,
                "type_beneficiaire": Patient.TypeBeneficiaire.PRINCIPAL,
            },
        )
        if not patient.plan_couverture:
            patient.plan_couverture = plan_standard
            patient.save(update_fields=["plan_couverture"])

        # Ayant droit rattaché à l'assuré
        ayant_droit, _ = Patient.objects.get_or_create(
            assure_principal=patient,
            prenom="Aminata",
            nom=patient.nom,
            defaults={
                "date_naissance": datetime.date(2018, 3, 22),
                "type_beneficiaire": Patient.TypeBeneficiaire.AYANT_DROIT,
                "lien_parente": Patient.LienParente.ENFANT,
                "plan_couverture": plan_standard,
            },
        )

        # 5. Service Médical tarifé
        service = ServiceMedical.objects.filter(
            nom="Consultation Médecine Générale",
            prestataire=hopital,
        ).first()
        if not service:
            service = ServiceMedical.objects.create(
                nom="Consultation Médecine Générale",
                prestataire=hopital,
                description="Consultation générale et bilan de santé régulier",
                prix=Decimal("15000.00"),
            )

        # 6. Rendez-vous de démonstration
        rdv = RendezVous.objects.filter(
            patient=patient,
            medecin=medecin,
            prestataire=hopital,
        ).first()
        if not rdv:
            date_rdv = timezone.now() + datetime.timedelta(days=2, hours=3)
            rdv = RendezVous.objects.create(
                patient=patient,
                medecin=medecin,
                prestataire=hopital,
                statut=RendezVous.Statut.CONFIRME,
                date_heure=date_rdv,
                motif="Contrôle tensionnel semestriel et renouvellement d'ordonnance",
            )

        # 7. Prise en charge, Consultation, Facturation et Ordonnance avec QR
        pec = PriseEnCharge.objects.filter(
            patient=patient,
            motif="Consultation de médecine générale et bilan de routine",
        ).first()
        if not pec:
            pec = PriseEnCharge.objects.create(
                patient=patient,
                motif="Consultation de médecine générale et bilan de routine",
                statut="validee",
            )
        elif pec.statut != "validee":
            pec.statut = "validee"
            pec.save(update_fields=["statut"])

        consultation = Consultation.objects.filter(
            patient=patient,
            medecin=medecin,
        ).first()
        if not consultation:
            date_consult = timezone.now() - datetime.timedelta(days=1)
            consultation = Consultation.objects.create(
                patient=patient,
                medecin=medecin,
                service=service,
                prise_en_charge=pec,
                date_consultation=date_consult,
                diagnostic="Suivi tensionnel stable. Bilan biologique de contrôle normal.",
                traitement="Poursuite des règles hygiéno-diététiques et traitement de fond.",
            )

        # Paiement associé
        paiement = Paiement.objects.filter(consultation=consultation).first()
        if not paiement:
            paiement = Paiement.objects.create(
                consultation=consultation,
                montant_total=Decimal("15000.00"),
                taux_applique=Decimal("80.00"),
                montant_part_assurance=Decimal("12000.00"),
                montant_part_patient=Decimal("3000.00"),
                statut=Paiement.Statut.REGLE,
                mode_reglement=Paiement.ModeReglement.ESPECES,
                date_reglement=consultation.date_consultation,
                enregistre_par=utilisateurs[User.Role.ADMIN],
            )

        # Ordonnance active prête pour le scan en pharmacie
        ordonnance = Ordonnance.objects.filter(consultation=consultation).first()
        if not ordonnance:
            ordonnance = Ordonnance.objects.create(
                consultation=consultation,
                statut=Ordonnance.Statut.ACTIF,
            )

        if not ordonnance.lignes.exists():
            LigneOrdonnance.objects.create(
                ordonnance=ordonnance,
                medicament="Paracétamol 1g",
                posologie="1 comprimé 3 fois par jour si douleur ou fièvre",
                duree="5 jours",
                quantite="1 boîte",
            )
            LigneOrdonnance.objects.create(
                ordonnance=ordonnance,
                medicament="Amoxicilline 500mg",
                posologie="1 gélule matin et soir au milieu des repas",
                duree="7 jours",
                quantite="2 boîtes",
            )

        self.stdout.write(
            self.style.SUCCESS(
                "\nDonnées de démonstration SantéSN initialisées avec succès !\n"
                "----------------------------------------------------------\n"
                f"Mot de passe unifié pour tous les comptes : {mot_de_passe}\n"
                "1. Administrateur  : admin@santesn.sn\n"
                "2. Médecin         : medecin@santesn.sn\n"
                "3. Pharmacien      : pharmacien@santesn.sn\n"
                "4. Assuré          : assure@santesn.sn\n"
                f"Ordonnance de test : {ordonnance.code_qr}\n"
                f"Carte Assuré       : {patient.numero_carte}\n"
                "----------------------------------------------------------"
            )
        )
