from django.core.management.base import BaseCommand
from django.db import transaction

from Plateform_medicale.models import (
    Medecin,
    Patient,
    Pharmacien,
    User,
)


class Command(BaseCommand):
    help = "Supprime les comptes de test/demonstration (@santesn.sn) et leurs donnees associees."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche uniquement les comptes qui seraient supprimes sans les supprimer.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        emails_demo = [
            "admin@santesn.sn",
            "medecin@santesn.sn",
            "pharmacien@santesn.sn",
            "assure@santesn.sn",
        ]

        comptes = User.objects.filter(email__in=emails_demo)
        nb_comptes = comptes.count()

        if nb_comptes == 0:
            self.stdout.write(self.style.SUCCESS("Aucun compte de test local trouve."))
            return

        self.stdout.write(f"Comptes de test locaux detectes ({nb_comptes}) :")
        for c in comptes:
            self.stdout.write(f"  - {c.email} (Role: {c.role})")

        if dry_run:
            self.stdout.write(self.style.WARNING("Mode simulation (--dry-run) : aucune modification effectuee."))
            return

        with transaction.atomic():
            for u in comptes:
                if hasattr(u, "patient"):
                    Patient.objects.filter(id=u.patient.id).delete()
                if hasattr(u, "medecin"):
                    Medecin.objects.filter(id=u.medecin.id).delete()
                if hasattr(u, "pharmacien"):
                    Pharmacien.objects.filter(id=u.pharmacien.id).delete()
                u.delete()

        self.stdout.write(self.style.SUCCESS(f"{nb_comptes} comptes de test locaux supprimes avec succes."))
