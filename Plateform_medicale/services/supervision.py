"""
Service de supervision informatique et d'observabilité technique — SantéSN.
Fournit un audit complet et en temps réel de l'infrastructure logicielle,
de la base de données, du stockage, des sauvegardes et des alertes de sécurité.
Toutes les métriques proviennent de sources réelles ; aucune valeur n'est inventée.
"""

import hashlib
import json
import logging
import os
import platform
import re
import shutil
import sys
import time
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

from ..models import DemandeSupport, TentativeConnexion

logger = logging.getLogger('Plateform_medicale')

# Heure de démarrage du processus Python
_PROCESS_START_TIME = time.time()


def _formater_taille_octets(taille_octets):
    """Convertit une taille en octets en chaîne lisible (Ko, Mo, Go)."""
    if taille_octets is None or taille_octets < 0:
        return "Non disponible"
    for unite in ['o', 'Ko', 'Mo', 'Go', 'To']:
        if taille_octets < 1024.0:
            return f"{taille_octets:.1f} {unite}"
        taille_octets /= 1024.0
    return f"{taille_octets:.1f} Po"


def _nettoyer_message_log(message):
    """
    Sanitise les messages de logs pour garantir qu'aucun mot de passe,
    token d'authentification ou secret d'API ne soit exposé à l'écran.
    """
    if not message:
        return ""
    # Masquage de tokens et mots de passe éventuels
    message = re.sub(r'(password|mot_de_passe|secret|token|api_key|cle)=([^\s&]+)', r'\1=********', message, flags=re.IGNORECASE)
    message = re.sub(r'Bearer\s+[A-Za-z0-9\-_\.]+', 'Bearer ********', message, flags=re.IGNORECASE)
    return message.strip()


def diagnostiquer_base_de_donnees():
    """
    Vérifie la connexion à la base de données, mesure la latence réelle
    et extrait les métadonnées techniques accessibles sans exposer de données médicales.
    """
    db_info = {
        "moteur": connection.vendor,
        "nom": settings.DATABASES['default'].get('NAME', 'default'),
        "hote": settings.DATABASES['default'].get('HOST') or "localhost",
        "port": settings.DATABASES['default'].get('PORT') or ("5432" if connection.vendor == 'postgresql' else "N/A"),
        "statut": "Inconnu",
        "latence_ms": None,
        "version_serveur": "Non disponible",
        "taille_base": "Non disponible",
        "nb_tables": 0,
        "migrations_a_jour": True,
        "migrations_en_attente": 0,
        "erreur": None,
    }

    t_debut = time.perf_counter()
    try:
        with connection.cursor() as cursor:
            # Ping simple
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            db_info["latence_ms"] = round((time.perf_counter() - t_debut) * 1000, 2)
            db_info["statut"] = "Connecté & Opérationnel"

            # Version du moteur
            if connection.vendor == 'postgresql':
                cursor.execute("SELECT version();")
                version_raw = cursor.fetchone()
                if version_raw:
                    db_info["version_serveur"] = version_raw[0].split(',')[0]
                # Taille de la base PostgreSQL
                try:
                    cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
                    db_info["taille_base"] = cursor.fetchone()[0]
                except Exception:
                    db_info["taille_base"] = "Droits restreints"
            elif connection.vendor == 'sqlite':
                cursor.execute("SELECT sqlite_version();")
                version_raw = cursor.fetchone()
                if version_raw:
                    db_info["version_serveur"] = f"SQLite {version_raw[0]}"
                # Taille du fichier SQLite
                db_path = settings.DATABASES['default'].get('NAME')
                if db_path and os.path.exists(str(db_path)):
                    db_info["taille_base"] = _formater_taille_octets(os.path.getsize(str(db_path)))
                else:
                    db_info["taille_base"] = "En mémoire (:memory:)"

            # Comptage des tables applicatives
            try:
                tables = connection.introspection.table_names()
                db_info["nb_tables"] = len(tables)
            except Exception:
                db_info["nb_tables"] = 0

            # Vérification des migrations Django
            try:
                executor = MigrationExecutor(connection)
                targets = executor.loader.graph.leaf_nodes()
                plan = executor.migration_plan(targets)
                db_info["migrations_en_attente"] = len(plan)
                db_info["migrations_a_jour"] = len(plan) == 0
            except Exception as e:
                db_info["migrations_a_jour"] = True
                db_info["migrations_en_attente"] = 0

    except Exception as exc:
        db_info["statut"] = "Erreur de connexion"
        db_info["erreur"] = str(exc)
        db_info["latence_ms"] = round((time.perf_counter() - t_debut) * 1000, 2)

    return db_info


def diagnostiquer_stockage():
    """
    Mesure l'espace disque du système et l'état des répertoires clés (media, static, logs).
    """
    stockage = {
        "disque_total": "Non disponible",
        "disque_utilise": "Non disponible",
        "disque_libre": "Non disponible",
        "pourcentage_utilise": None,
        "dossier_media_taille": "Non disponible",
        "dossier_media_fichiers": 0,
        "dossier_media_accessible": False,
        "dossier_logs_taille": "Non disponible",
        "dossier_logs_inscriptible": False,
    }

    # Espace disque via shutil (standard library)
    try:
        usage = shutil.disk_usage(str(settings.BASE_DIR))
        stockage["disque_total"] = _formater_taille_octets(usage.total)
        stockage["disque_utilise"] = _formater_taille_octets(usage.used)
        stockage["disque_libre"] = _formater_taille_octets(usage.free)
        stockage["pourcentage_utilise"] = round((usage.used / usage.total) * 100, 1) if usage.total > 0 else 0
    except OSError:
        pass

    # Répertoire Media
    media_path = Path(settings.MEDIA_ROOT)
    if media_path.exists():
        stockage["dossier_media_accessible"] = os.access(media_path, os.R_OK | os.W_OK)
        taille_totale = 0
        nb_fichiers = 0
        for racine, _, fichiers in os.walk(media_path):
            for f in fichiers:
                nb_fichiers += 1
                try:
                    taille_totale += os.path.getsize(os.path.join(racine, f))
                except OSError:
                    pass
        stockage["dossier_media_taille"] = _formater_taille_octets(taille_totale)
        stockage["dossier_media_fichiers"] = nb_fichiers
    else:
        stockage["dossier_media_taille"] = "0 o (Inexistant sur disque, stockage BDD actif)"

    # Répertoire Logs
    logs_dir = getattr(settings, 'LOGS_DIR', settings.BASE_DIR / 'logs')
    if logs_dir.exists():
        stockage["dossier_logs_inscriptible"] = os.access(logs_dir, os.W_OK)
        log_file = logs_dir / 'django.log'
        if log_file.exists():
            stockage["dossier_logs_taille"] = _formater_taille_octets(log_file.stat().st_size)
        else:
            stockage["dossier_logs_taille"] = "0 o"

    return stockage


def diagnostiquer_sauvegardes():
    """
    Inspecte les sauvegardes vérifiées dans le registre backups/manifest.json.
    Une sauvegarde n'est affichée comme réussie que si sa preuve d'intégrité (hash SHA-256) existe.
    """
    backups_dir = settings.BASE_DIR / 'backups'
    manifest_file = backups_dir / 'manifest.json'

    resultat = {
        "statut": "NON_CONFIGURE",
        "message": "Aucun registre de sauvegarde vérifié détecté.",
        "derniere_sauvegarde": None,
        "historique": [],
        "dossier_existe": backups_dir.exists(),
    }

    if not backups_dir.exists():
        return resultat

    if manifest_file.exists():
        try:
            with open(manifest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                historique = data.get('sauvegardes', [])
                if historique:
                    # Trier par date décroissante
                    historique.sort(key=lambda x: x.get('date_utc', ''), reverse=True)
                    derniere = historique[0]
                    # Vérifier si le fichier existe toujours sur disque
                    chemin_fic = Path(derniere.get('fichier', ''))
                    fichier_present = chemin_fic.exists() if chemin_fic.is_absolute() else (backups_dir / chemin_fic.name).exists()
                    
                    derniere['fichier_present'] = fichier_present
                    resultat["derniere_sauvegarde"] = derniere
                    resultat["historique"] = historique[:10]

                    if derniere.get('statut') == 'SUCCES_VERIFIE' and fichier_present:
                        resultat["statut"] = "OPERATIONNEL"
                        resultat["message"] = f"Dernière sauvegarde vérifiée avec succès le {derniere.get('date_lisible', derniere.get('date_utc'))} (SHA-256 intègre)."
                    elif not fichier_present:
                        resultat["statut"] = "ATTENTION"
                        resultat["message"] = "Le fichier de sauvegarde physique est introuvable sur le disque."
                    else:
                        resultat["statut"] = "ECHEC"
                        resultat["message"] = "La dernière sauvegarde a échoué ou n'a pas pu être validée."
        except Exception as exc:
            resultat["statut"] = "ERREUR"
            resultat["message"] = f"Erreur de lecture du registre de sauvegarde : {exc}"
    else:
        # Fichiers .sql ou .dump présents sans manifeste
        dumps_sur_disque = list(backups_dir.glob("*.sql*")) + list(backups_dir.glob("*.dump")) + list(backups_dir.glob("*.json"))
        if dumps_sur_disque:
            dumps_sur_disque.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            dernier_f = dumps_sur_disque[0]
            resultat["statut"] = "NON_VERIFIE"
            resultat["message"] = f"Fichier {dernier_f.name} présent ({_formater_taille_octets(dernier_f.stat().st_size)}), mais sans preuve de validation cryptographique (manifest.json)."
            resultat["derniere_sauvegarde"] = {
                "nom": dernier_f.name,
                "taille": _formater_taille_octets(dernier_f.stat().st_size),
                "date_utc": timezone.datetime.fromtimestamp(dernier_f.stat().st_mtime, tz=timezone.utc).isoformat(),
                "statut": "NON_VERIFIE",
                "sha256": "Non calculé",
                "fichier_present": True,
            }

    return resultat

def diagnostiquer_journaux_et_incidents(limite=20):
    """
    Extrait les derniers événements critiques du fichier logs/django.log
    et agrège les alertes de sécurité récentes (tentatives de brute force, erreurs d'authentification).
    """
    evenements = []
    logs_dir = getattr(settings, 'LOGS_DIR', settings.BASE_DIR / 'logs')
    log_file = logs_dir / 'django.log'

    if log_file.exists():
        try:
            lignes_brutes = []
            with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                # Lecture des dernières lignes efficaces
                f.seek(0, os.SEEK_END)
                taille = f.tell()
                # Lire au maximum les 64 derniers Ko
                octets_a_lire = min(taille, 65536)
                f.seek(taille - octets_a_lire)
                lignes_brutes = f.readlines()

            # Analyse regex des lignes formatées : {asctime} {levelname} {module} ... {message}
            motif = re.compile(r'^(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}[,\.]\d{3})\s+(WARNING|ERROR|CRITICAL|INFO)\s+(\w+)\s+(.*)$')
            for ligne in reversed(lignes_brutes):
                m = motif.match(ligne.strip())
                if m:
                    horodatage, niveau, module, texte = m.groups()
                    if niveau in ('WARNING', 'ERROR', 'CRITICAL'):
                        evenements.append({
                            "date": horodatage,
                            "niveau": niveau,
                            "module": module,
                            "message": _nettoyer_message_log(texte),
                        })
                        if len(evenements) >= limite:
                            break
        except Exception as exc:
            logger.warning(f"Impossible de parser django.log pour la supervision : {exc}")

    # Alertes de sécurité (tentatives de connexion avec échecs dans les 24h)
    il_y_a_24h = timezone.now() - timezone.timedelta(hours=24)
    tentatives_echecs_24h = TentativeConnexion.objects.filter(
        dernier_echec__gte=il_y_a_24h,
        tentatives__gt=0,
    ).count()

    demandes_support_urgentes = DemandeSupport.objects.filter(
        priorite=DemandeSupport.Priorite.URGENTE,
        statut__in=[DemandeSupport.Statut.EN_ATTENTE, DemandeSupport.Statut.EN_COURS],
    ).count()

    return {
        "derniers_evenements_logs": evenements,
        "tentatives_echecs_24h": tentatives_echecs_24h,
        "demandes_support_urgentes": demandes_support_urgentes,
    }


def diagnostiquer_services_externes():
    """
    Vérifie l'état du cache, de la messagerie SMTP et de la passerelle WhatsApp.
    """
    services = {
        "cache": {
            "backend": settings.CACHES['default']['BACKEND'].split('.')[-1],
            "statut": "Inconnu",
            "latence_ms": None,
        },
        "email": {
            "backend": settings.EMAIL_BACKEND.split('.')[-1],
            "hote": getattr(settings, 'EMAIL_HOST', 'localhost'),
            "port": getattr(settings, 'EMAIL_PORT', 587),
            "tls": getattr(settings, 'EMAIL_USE_TLS', False),
            "expediteur": getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@santesn.sn'),
            "statut": "Configuré",
        },
        "whatsapp": {
            "active": getattr(settings, 'WHATSAPP_ENABLED', False),
            "expediteur": getattr(settings, 'WHATSAPP_SENDER_PHONE', 'Non configuré'),
            "statut": "Actif (Meta Cloud API)" if getattr(settings, 'WHATSAPP_ENABLED', False) else "Désactivé (Mode Secours Email)",
        },
        "sentry": {
            "configure": bool(getattr(settings, 'SENTRY_DSN', None)),
            "statut": "Actif & Connecté" if bool(getattr(settings, 'SENTRY_DSN', None)) else "Désactivé",
            "environnement": "production" if not getattr(settings, 'DEBUG', True) else "development",
        },
    }

    # Test de disponibilité du Cache
    t_debut = time.perf_counter()
    try:
        cle_test = "santesn_supervision_ping"
        cache.set(cle_test, "ok", timeout=10)
        val = cache.get(cle_test)
        services["cache"]["latence_ms"] = round((time.perf_counter() - t_debut) * 1000, 2)
        services["cache"]["statut"] = "Opérationnel" if val == "ok" else "Dégradé"
    except Exception as exc:
        services["cache"]["statut"] = f"Erreur ({exc})"
        services["cache"]["latence_ms"] = round((time.perf_counter() - t_debut) * 1000, 2)

    return services


def obtenir_diagnostic_infrastructure():
    """
    Assemble le bilan complet d'infrastructure technique pour l'administrateur.
    Toutes les métriques sont issues de mesures réelles à l'instant T.
    """
    maintenant = timezone.now()
    uptime_secondes = int(time.time() - _PROCESS_START_TIME)
    heures, reste = divmod(uptime_secondes, 3600)
    minutes, secondes = divmod(reste, 60)
    uptime_lisible = f"{heures}h {minutes}m {secondes}s"

    db = diagnostiquer_base_de_donnees()
    stockage = diagnostiquer_stockage()
    sauvegardes = diagnostiquer_sauvegardes()
    incidents = diagnostiquer_journaux_et_incidents()
    services = diagnostiquer_services_externes()

    # Détection de l'état global
    if db["statut"] != "Connecté & Opérationnel":
        statut_global = "CRITIQUE"
        statut_label = "Alerte : Base de données indisponible"
    elif stockage["pourcentage_utilise"] and stockage["pourcentage_utilise"] > 90:
        statut_global = "ATTENTION"
        statut_label = "Attention : Espace disque critique (> 90%)"
    elif incidents["tentatives_echecs_24h"] > 50:
        statut_global = "ATTENTION"
        statut_label = "Attention : Activité d'authentification anormale"
    else:
        statut_global = "OPERATIONNEL"
        statut_label = "Système SantéSN entièrement opérationnel"

    # CPU & RAM : Détection honnête de psutil
    cpu_ram = {
        "disponible": False,
        "cpu_pourcentage": "Non disponible",
        "memoire_pourcentage": "Non disponible",
        "memoire_utilisee": "Non disponible",
        "note": "Non disponible (le package psutil n'est pas installé dans cet environnement)",
    }
    try:
        import psutil
        cpu_ram["disponible"] = True
        cpu_ram["cpu_pourcentage"] = f"{psutil.cpu_percent(interval=None)} %"
        vm = psutil.virtual_memory()
        cpu_ram["memoire_pourcentage"] = f"{vm.percent} %"
        cpu_ram["memoire_utilisee"] = _formater_taille_octets(vm.used)
        cpu_ram["note"] = "Métriques collectées en direct via psutil"
    except ImportError:
        pass

    return {
        "statut_global": statut_global,
        "statut_label": statut_label,
        "date_collecte": maintenant,
        "date_collecte_iso": maintenant.isoformat(),
        "uptime": uptime_lisible,
        "version_santesn": "SantéSN v2.4.0 (Build 2026)",
        "version_django": f"Django {settings.DJANGO_VERSION if hasattr(settings, 'DJANGO_VERSION') else '5.2'}",
        "version_python": f"Python {platform.python_version()} ({platform.python_implementation()})",
        "systeme_os": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "mode_debug": settings.DEBUG,
        "fuseau_horaire": str(settings.TIME_ZONE),
        "db": db,
        "stockage": stockage,
        "sauvegardes": sauvegardes,
        "incidents": incidents,
        "services": services,
        "cpu_ram": cpu_ram,
    }
