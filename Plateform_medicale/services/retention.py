# -*- coding: utf-8 -*-
"""
Service de rétention et de maintenance automatique des données (Cycle 30 jours / 1 mois).
Purger les sessions expirées, les anciennes notifications lues, les tentatives obsolètes
et réinitialiser de façon idempotente les comptes et données de test locaux.
"""

import datetime
import logging
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from ..models import Notification, TentativeConnexion

logger = logging.getLogger(__name__)

CLE_CACHE_DERNIERE_PURGE = "santesn_derniere_purge_donnees"


def obtenir_metriques_retention(jours=30):
    """Calcule le volume des donnees temporaires pretes a etre purgees."""
    maintenant = timezone.now()
    limite = maintenant - datetime.timedelta(days=jours)

    # 1. Sessions expirées
    nb_sessions = 0
    try:
        from django.contrib.sessions.models import Session
        nb_sessions = Session.objects.filter(expire_date__lt=maintenant).count()
    except Exception as exc:
        logger.warning("Impossible de compter les sessions expirees : %s", exc)

    # 2. Notifications lues et anciennes
    nb_notifications = Notification.objects.filter(
        lue=True, date_creation__lt=limite
    ).count()

    # 3. Tentatives de connexion obsolètes (> jours)
    nb_tentatives = TentativeConnexion.objects.filter(
        dernier_echec__lt=limite
    ).count()

    derniere_purge_str = cache.get(CLE_CACHE_DERNIERE_PURGE)

    return {
        "jours_retention": jours,
        "sessions_expirees": nb_sessions,
        "notifications_anciennes": nb_notifications,
        "tentatives_obsoletes": nb_tentatives,
        "total_a_purger": nb_sessions + nb_notifications + nb_tentatives,
        "derniere_purge": derniere_purge_str,
    }


def purger_donnees_obsoletes(
    jours=30,
    purger_sessions=True,
    purger_notifs=True,
    purger_tentatives=True,
    reinitialiser_demo=False,
    dry_run=False,
):
    """
    Exécute la purge des données temporaires au-delà de la durée de rétention.
    Si dry_run=True, ne supprime rien et retourne les compteurs d'éléments concernés.
    """
    maintenant = timezone.now()
    limite = maintenant - datetime.timedelta(days=jours)

    resultats = {
        "jours": jours,
        "sessions": 0,
        "notifications": 0,
        "tentatives": 0,
        "demo_reinitialisee": False,
        "dry_run": dry_run,
    }

    # 1. Sessions Django expirées
    if purger_sessions:
        try:
            from django.contrib.sessions.models import Session
            from django.core.management import call_command
            nb_sessions = Session.objects.filter(expire_date__lt=maintenant).count()
            resultats["sessions"] = nb_sessions
            if not dry_run and nb_sessions > 0:
                call_command("clearsessions")
        except Exception as exc:
            logger.warning("Erreur lors de la purge des sessions expirees : %s", exc)

    # 2. Notifications lues de plus de 30 jours
    if purger_notifs:
        qs_notifs = Notification.objects.filter(lue=True, date_creation__lt=limite)
        resultats["notifications"] = qs_notifs.count()
        if not dry_run and resultats["notifications"] > 0:
            qs_notifs.delete()

    # 3. Tentatives de connexion obsolètes
    if purger_tentatives:
        qs_tentatives = TentativeConnexion.objects.filter(dernier_echec__lt=limite)
        resultats["tentatives"] = qs_tentatives.count()
        if not dry_run and resultats["tentatives"] > 0:
            qs_tentatives.delete()

    # 4. Réinitialisation des données de test
    if reinitialiser_demo and not dry_run:
        try:
            from django.core.management import call_command
            call_command("seed_demo")
            resultats["demo_reinitialisee"] = True
        except Exception as exc:
            logger.error("Erreur lors de la reinitialisation demo : %s", exc)

    if not dry_run:
        horodatage = maintenant.strftime("%d/%m/%Y à %H:%M")
        cache.set(CLE_CACHE_DERNIERE_PURGE, horodatage, timeout=None)
        resultats["derniere_purge"] = horodatage

    return resultats


def verifier_et_executer_auto_purge(jours=30):
    """
    Vérification automatique périodique (au maximum 1 fois toutes les 24 heures).
    S'exécute de façon transparente en arrière-plan sans bloquer les requêtes.
    """
    cle_verif = "santesn_derniere_verif_auto_purge"
    if cache.get(cle_verif):
        return None

    # Marquer la vérification comme effectuée pour les prochaines 24 heures
    cache.set(cle_verif, "1", timeout=86400)

    try:
        return purger_donnees_obsoletes(
            jours=jours,
            purger_sessions=True,
            purger_notifs=True,
            purger_tentatives=True,
            reinitialiser_demo=False,
            dry_run=False,
        )
    except Exception as exc:
        logger.warning("Échec de la purge automatique en arriere-plan : %s", exc)
        return None
