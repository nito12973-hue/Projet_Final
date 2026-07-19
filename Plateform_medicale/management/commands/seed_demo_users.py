import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from Plateform_medicale.forms import lier_fiche_medecin, lier_fiche_pharmacien
from Plateform_medicale.models import User


class Command(BaseCommand):
    help = "Cree des comptes de demonstration SanteSN pour chaque role (developpement local uniquement)."

    DEFAULT_PASSWORD = "SanteSN2026!"

    ROLE_CONFIG = {
        User.Role.ASSURE: ("assure", "Assure", "Demo"),
        User.Role.MEDECIN: ("medecin", "Medecin", "Demo"),
        User.Role.PHARMACIEN: ("pharmacien", "Pharmacien", "Demo"),
    }

    SPECIALITES_DEMO = [
        "Medecine generale",
        "Pediatrie",
        "Gynecologie",
        "Cardiologie",
        "Dermatologie",
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=12,
            help="Nombre d'utilisateurs a creer pour chaque role non-admin.",
        )
        parser.add_argument(
            "--password",
            default=None,
            help=(
                "Mot de passe commun des comptes de demo. Par defaut, la variable "
                "d'environnement SANTESN_DEMO_PASSWORD, sinon le mot de passe de "
                "demo documente dans DEMO_USERS.md."
            ),
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "seed_demo_users est reserve au developpement local (DEBUG=True). "
                "Il ne doit jamais etre execute sur un environnement de production."
            )

        password = (
            options["password"]
            or os.environ.get("SANTESN_DEMO_PASSWORD")
            or self.DEFAULT_PASSWORD
        )

        count = options["count"]
        created = 0
        updated = 0

        admin, was_created = User.objects.get_or_create(
            email="admin@santesn.local",
            defaults={
                "first_name": "Admin",
                "last_name": "SanteSN",
                "phone_number": "+221770000000",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.role = User.Role.ADMIN
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password(password)
        admin.save()
        created += int(was_created)
        updated += int(not was_created)

        for role, (prefix, first_name, last_name) in self.ROLE_CONFIG.items():
            for index in range(1, count + 1):
                email = f"{prefix}{index:02d}@santesn.local"
                user, was_created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "first_name": f"{first_name} {index:02d}",
                        "last_name": last_name,
                        "phone_number": f"+22177{index:07d}",
                        "role": role,
                    },
                )
                user.first_name = f"{first_name} {index:02d}"
                user.last_name = last_name
                user.phone_number = f"+22177{index:07d}"
                user.role = role
                user.is_active = True
                user.is_staff = False
                user.is_superuser = False
                user.set_password(password)
                user.save()
                lier_fiche_medecin(user)
                lier_fiche_pharmacien(user)
                if role == User.Role.MEDECIN and hasattr(user, "medecin") and not user.medecin.specialite:
                    user.medecin.specialite = self.SPECIALITES_DEMO[(index - 1) % len(self.SPECIALITES_DEMO)]
                    user.medecin.save(update_fields=["specialite"])
                created += int(was_created)
                updated += int(not was_created)

        self.stdout.write(self.style.SUCCESS("Comptes de demonstration prets."))
        self.stdout.write(f"Crees: {created} | Mis a jour: {updated}")
        self.stdout.write(f"Mot de passe commun: {password}")
        self.stdout.write("Admin: admin@santesn.local")
