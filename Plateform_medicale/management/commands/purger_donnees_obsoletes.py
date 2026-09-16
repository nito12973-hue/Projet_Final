# -*- coding: utf-8 -*-
"""
Commande Django pour purger les donnees temporaires et obsoletes (> 30 jours).
"""

from django.core.management.base import BaseCommand
from Plateform_medicale.services.retention import purger_donnees_obsoletes


class Command(BaseCommand):
    help = "Purge les données temporaires (> 30 jours : sessions expirées, notifications lues, tentatives obsolètes)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--jours",
            type=int,
            default=30,
            help="Délai de rétention en jours (par défaut : 30 jours / 1 mois).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simule le nettoyage sans supprimer aucune donnée.",
        )

    def handle(self, *args, **options):
        jours = options["jours"]
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING(f"--- SIMULATION (Dry Run) : Rétention {jours} jours ---"))
        else:
            self.stdout.write(self.style.NOTICE(f"--- Purge des données temporaires (> {jours} jours) ---"))

        resultats = purger_donnees_obsoletes(
            jours=jours,
            purger_sessions=True,
            purger_notifs=True,
            purger_tentatives=True,
            dry_run=dry_run,
        )

        self.stdout.write(f"  - Sessions Django expirées : {resultats['sessions']}")
        self.stdout.write(f"  - Notifications lues (> {jours} j) : {resultats['notifications']}")
        self.stdout.write(f"  - Tentatives de connexion obsolètes : {resultats['tentatives']}")

        total = resultats["sessions"] + resultats["notifications"] + resultats["tentatives"]
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"Simulation terminée : {total} élément(s) éligible(s) à la purge."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Purge terminée avec succès : {total} élément(s) supprimé(s)."))
