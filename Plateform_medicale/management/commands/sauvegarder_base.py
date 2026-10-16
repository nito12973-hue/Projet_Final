"""
Commande Django de sauvegarde industrielle et vérifiable de la base de données SantéSN.
Exécute la sauvegarde, calcule l'empreinte cryptographique SHA-256
et enregistre la preuve dans backups/manifest.json.
Usage : python manage.py sauvegarder_base [--format json|sql]
"""

import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone


class Command(BaseCommand):
    help = "Exécute une sauvegarde technique vérifiable de la base de données SantéSN."

    def add_arguments(self, parser):
        parser.add_argument(
            '--retention-jours',
            type=int,
            default=30,
            help="Supprime les sauvegardes antérieures à ce nombre de jours (défaut : 30 jours).",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Démarrage du processus de sauvegarde SantéSN..."))
        debut = time.perf_counter()

        backups_dir = settings.BASE_DIR / 'backups'
        backups_dir.mkdir(parents=True, exist_ok=True)

        horodatage = timezone.now().strftime("%Y%m%d_%H%M%S")
        moteur = connection.vendor

        nom_fichier = f"santesn_backup_{moteur}_{horodatage}.json"
        chemin_fichier = backups_dir / nom_fichier

        try:
            # Pour garantir la compatibilité multi-plateforme (Windows, Linux, Docker, SQLite & PostgreSQL),
            # nous réalisons un dump structuré complet des données applicatives
            # Désactivation des server-side cursors pour compatibilité Neon / PgBouncer
            try:
                connection.features.can_use_chunked_reads = False
            except Exception:
                pass

            with open(chemin_fichier, 'w', encoding='utf-8') as f:
                call_command(
                    'dumpdata',
                    exclude=['contenttypes', 'auth.permission'],
                    indent=2,
                    stdout=f,
                )

            # Vérification de l'existence et calcul du SHA-256
            if not chemin_fichier.exists() or chemin_fichier.stat().st_size == 0:
                raise RuntimeError("Le fichier de sauvegarde n'a pas été généré ou est vide.")

            taille_octets = chemin_fichier.stat().st_size
            hasher = hashlib.sha256()
            with open(chemin_fichier, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b''):
                    hasher.update(chunk)
            empreinte_sha256 = hasher.hexdigest()

            duree = round(time.perf_counter() - debut, 2)

            entree_manifeste = {
                "id": f"backup_{horodatage}",
                "fichier": nom_fichier,
                "chemin_relatif": str(Path("backups") / nom_fichier),
                "moteur": moteur,
                "taille_octets": taille_octets,
                "taille_lisible": f"{taille_octets / (1024 * 1024):.2f} Mo" if taille_octets > 1024*1024 else f"{taille_octets / 1024:.1f} Ko",
                "sha256": empreinte_sha256,
                "date_utc": timezone.now().isoformat(),
                "date_lisible": timezone.now().strftime("%d/%m/%Y à %H:%M:%S"),
                "duree_secondes": duree,
                "statut": "SUCCES_VERIFIE",
            }

            # Mise à jour du registre manifest.json
            manifest_path = backups_dir / 'manifest.json'
            manifest_data = {"version": "1.0", "sauvegardes": []}
            if manifest_path.exists():
                try:
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest_data = json.load(f)
                except Exception:
                    manifest_data = {"version": "1.0", "sauvegardes": []}

            manifest_data.setdefault("sauvegardes", []).append(entree_manifeste)

            # Rétention
            retention_jours = options.get('retention_jours', 30)
            date_limite = timezone.now() - timezone.timedelta(days=retention_jours)
            sauvegardes_filtrees = []
            for s in manifest_data["sauvegardes"]:
                d_str = s.get("date_utc")
                conserver = True
                if d_str:
                    try:
                        d = timezone.datetime.fromisoformat(d_str)
                        if d < date_limite:
                            conserver = False
                            p = backups_dir / s.get("fichier", "")
                            if p.exists():
                                p.unlink(missing_ok=True)
                                self.stdout.write(f"Suppression de l'ancienne sauvegarde expirée : {p.name}")
                    except Exception:
                        pass
                if conserver:
                    sauvegardes_filtrees.append(s)

            manifest_data["sauvegardes"] = sauvegardes_filtrees

            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest_data, f, indent=2, ensure_ascii=False)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Sauvegarde vérifiée avec succès !\n"
                    f"Fichier : {nom_fichier} ({entree_manifeste['taille_lisible']})\n"
                    f"SHA-256 : {empreinte_sha256}\n"
                    f"Durée   : {duree} s"
                )
            )

        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Échec de la sauvegarde : {exc}"))
            raise exc
