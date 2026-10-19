"""
Vues de supervision informatique et d'observabilité technique — SantéSN.
Espace réservé aux administrateurs autorisés pour auditer l'infrastructure technique,
la santé des processus, de la base de données, du stockage et des sauvegardes.
"""

import json
from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone

from ..models import User
from ..services.supervision import (
    diagnostiquer_base_de_donnees,
    diagnostiquer_services_externes,
    obtenir_diagnostic_infrastructure,
)
from .utils import admin_required


@admin_required
def supervision_systeme(request):
    """
    Tableau de bord de supervision technique réservé à l'administrateur SantéSN.
    Supporte le rendu HTML interactif et l'export JSON.
    """
    diagnostic = obtenir_diagnostic_infrastructure()

    if request.GET.get('format') == 'json' or 'application/json' in request.headers.get('Accept', ''):
        # Sérialisation JSON sûre (dates en ISO)
        def _serialize(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            return str(obj)

        return JsonResponse(diagnostic, safe=False, json_dumps_params={'default': _serialize, 'indent': 2})

    return render(request, "supervision_systeme.html", {
        "diag": diagnostic,
        "page_titre": "Supervision Technique & Infrastructure",
    })


@admin_required
def tester_sentry(request):
    """
    Déclenche un événement de test et une exception contrôlée vers Sentry
    pour permettre à l'administrateur de vérifier la réception dans sa console Sentry.
    """
    import sentry_sdk
    from django.contrib import messages
    from django.shortcuts import redirect

    if not getattr(settings, 'SENTRY_DSN', None):
        messages.error(request, "Sentry n'est pas configuré (aucun SENTRY_DSN défini).")
        return redirect('supervision_systeme')

    try:
        # Envoi d'un message d'information
        msg_id = sentry_sdk.capture_message(f"SantéSN Test Admin déclenché par {request.user.email}")
        
        # Envoi d'une exception de test
        try:
            raise ValueError(f"SantéSN Test Alert : Validation de connexion Sentry réussie (Admin: {request.user.email})")
        except ValueError as exc:
            exc_id = sentry_sdk.capture_exception(exc)
        
        sentry_sdk.flush(timeout=4.0)
        messages.success(request, f"Événement de test transmis à Sentry avec succès (Event ID: {exc_id or msg_id}). Rafraîchissez votre tableau de bord Sentry.")
    except Exception as e:
        messages.error(request, f"Erreur lors de l'envoi vers Sentry : {e}")

    return redirect('supervision_systeme')


def health_check(request):
    """
    Contrôle de santé DevOps (Healthcheck Probe) pour Docker, Nginx, Kubernetes et monitoring externe.
    Ne divulgue aucun secret ni donnée sensible.
    Retourne HTTP 200 si la base est opérationnelle, HTTP 503 en cas d'incident critique.
    """
    db = diagnostiquer_base_de_donnees()
    services = diagnostiquer_services_externes()

    est_sain = db["statut"] == "Connecté & Opérationnel"
    code_statut = 200 if est_sain else 503

    payload = {
        "status": "healthy" if est_sain else "unhealthy",
        "service": "SantéSN Tiers-Payant Cloud",
        "timestamp": timezone.now().isoformat(),
        "database": {
            "status": "ok" if est_sain else "error",
            "vendor": db["moteur"],
            "latency_ms": db["latence_ms"],
        },
        "cache": {
            "status": "ok" if services["cache"]["statut"] == "Opérationnel" else "degraded",
            "latency_ms": services["cache"]["latence_ms"],
        },
    }

    return JsonResponse(payload, status=code_statut)


def metrics_prometheus(request):
    """
    Exposition native des métriques au format standard Prometheus (OpenMetrics).
    Consommable directement par un scraper Prometheus / Grafana sans dépendance lourde.
    Pour les navigateurs web, affiche TOUJOURS la console visuelle SantéSN intégrée.
    """
    from django.http import HttpResponse, HttpResponseForbidden
    from django.shortcuts import redirect
    from django.urls import reverse
    from ..models import (
        User, Patient, PriseEnCharge, Ordonnance, Paiement, Consultation,
        TentativeConnexion, JournalActivite
    )

    # Contrôle strict anti-usurpation : ne jamais faire confiance à HTTP_X_FORWARDED_FOR pour l'authentification réseau
    remote_addr = (request.META.get('REMOTE_ADDR', '') or '').strip()
    est_local = remote_addr in ('127.0.0.1', '::1')
    est_admin = request.user.is_authenticated and getattr(request.user, 'role', None) == User.Role.ADMIN

    # Support d'un jeton d'authentification Bearer dédié pour collecteurs distants (avec comparaison en temps constant)
    from django.utils.crypto import constant_time_compare
    auth_header = request.headers.get('Authorization', '').strip()
    metrics_token = getattr(settings, 'PROMETHEUS_METRICS_TOKEN', '')
    est_token_valide = bool(metrics_token) and constant_time_compare(auth_header, f"Bearer {metrics_token}")

    user_agent = request.headers.get('User-Agent', '').lower()
    accept = request.headers.get('Accept', '').lower()

    # Détection : la requête provient-elle d'un navigateur web (humain) ou d'un collecteur machine ?
    est_navigateur = ('text/html' in accept) or ('mozilla' in user_agent and 'prometheus' not in user_agent)

    # Règle stricte d'accès aux métriques d'infrastructure :
    # 1. Tout utilisateur connecté NON-ADMINISTRATEUR est strictement refoulé (403)
    if request.user.is_authenticated and not est_admin:
        return HttpResponseForbidden("Accès réservé aux administrateurs de la plateforme SantéSN.")

    if est_navigateur:
        # Pour les utilisateurs dans un navigateur, exiger une session Admin valide.
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.get_full_path()}")
        if not est_admin:
            return HttpResponseForbidden("Accès réservé aux administrateurs de la plateforme SantéSN.")
    else:
        # Collecteurs automatiques machine-to-machine
        if not (est_local or est_admin or est_token_valide):
            return HttpResponseForbidden("Accès réservé aux administrateurs ou collecteurs Prometheus autorisés.")

    db = diagnostiquer_base_de_donnees()
    services = diagnostiquer_services_externes()

    lignes = [
        "# HELP santesn_up Statut de disponibilite generale du systeme SanteSN (1 = up, 0 = down)",
        "# TYPE santesn_up gauge",
        f"santesn_up {1 if db['statut'] == 'Connecté & Opérationnel' else 0}",
        "",
        "# HELP santesn_database_latency_milliseconds Latence mesuree vers la base PostgreSQL en ms",
        "# TYPE santesn_database_latency_milliseconds gauge",
        f"santesn_database_latency_milliseconds {db.get('latence_ms', 0)}",
        "",
        "# HELP santesn_cache_latency_milliseconds Latence mesuree vers le cache applicatif en ms",
        "# TYPE santesn_cache_latency_milliseconds gauge",
        f"santesn_cache_latency_milliseconds {services['cache'].get('latence_ms', 0) or 0}",
        "",
        "# HELP santesn_total_users Nombre total d'utilisateurs par role",
        "# TYPE santesn_total_users gauge",
    ]

    # Décompte par rôle
    try:
        from django.db.models import Count
        roles_counts = User.objects.values('role').annotate(total=Count('id'))
        for rc in roles_counts:
            lignes.append(f'santesn_total_users{{role="{rc["role"]}"}} {rc["total"]}')
    except Exception:
        pass

    # Métriques métiers SantéSN
    try:
        nb_patients = Patient.objects.count()
        nb_pec_attente = PriseEnCharge.objects.filter(statut="en_attente").count()
        nb_pec_validees = PriseEnCharge.objects.filter(statut="validee").count()
        nb_ordonnances = Ordonnance.objects.count()
        nb_consultations = Consultation.objects.count()

        lignes.extend([
            "",
            "# HELP santesn_patients_total Nombre de patients assures enregistres",
            "# TYPE santesn_patients_total gauge",
            f"santesn_patients_total {nb_patients}",
            "",
            "# HELP santesn_prises_en_charge_total Prises en charge par statut",
            "# TYPE santesn_prises_en_charge_total gauge",
            f'santesn_prises_en_charge_total{{statut="en_attente"}} {nb_pec_attente}',
            f'santesn_prises_en_charge_total{{statut="validee"}} {nb_pec_validees}',
            "",
            "# HELP santesn_ordonnances_total Nombre total d'ordonnances emises",
            "# TYPE santesn_ordonnances_total gauge",
            f"santesn_ordonnances_total {nb_ordonnances}",
            "",
            "# HELP santesn_consultations_total Nombre total de consultations realisees",
            "# TYPE santesn_consultations_total gauge",
            f"santesn_consultations_total {nb_consultations}",
        ])
    except Exception:
        pass

    # Métriques de sécurité (échecs de connexion récentes)
    try:
        maintenant = timezone.now()
        h24 = maintenant - timezone.timedelta(hours=24)
        echecs_24h = TentativeConnexion.objects.filter(dernier_echec__gte=h24).count()
        lignes.extend([
            "",
            "# HELP santesn_security_failed_logins_24h Tentatives de connexion echouees sur les dernieres 24h",
            "# TYPE santesn_security_failed_logins_24h gauge",
            f"santesn_security_failed_logins_24h {echecs_24h}",
        ])
    except Exception:
        echecs_24h = 0

    lignes.append("")
    contenu_metrics = "\n".join(lignes)

    format_param = request.GET.get('format', '').lower()

    # Dans un navigateur web : TOUJOURS afficher la console graphique SantéSN avec design unifié,
    # même avec ?format=raw (pour ne JAMAIS afficher une page blanche de texte brut à l'utilisateur).
    if est_navigateur:
        roles_dict = {}
        try:
            from django.db.models import Count
            for rc in User.objects.values('role').annotate(total=Count('id')):
                roles_dict[rc['role']] = rc['total']
        except Exception:
            pass

        metriques_context = {
            "up": 1 if db['statut'] == 'Connecté & Opérationnel' else 0,
            "db_latence": db.get('latence_ms', 0),
            "cache_latence": services['cache'].get('latence_ms', 0) or 0,
            "security_failed_logins": echecs_24h,
            "roles": roles_dict,
            "patients": nb_patients if 'nb_patients' in locals() else 0,
            "pec_attente": nb_pec_attente if 'nb_pec_attente' in locals() else 0,
            "pec_validees": nb_pec_validees if 'nb_pec_validees' in locals() else 0,
            "ordonnances": nb_ordonnances if 'nb_ordonnances' in locals() else 0,
            "consultations": nb_consultations if 'nb_consultations' in locals() else 0,
            "flux_brut": contenu_metrics,
            "heure_mesure": timezone.now(),
            "format_raw_demande": format_param in ('raw', 'prometheus', 'text'),
        }
        return render(request, "metrics_prometheus.html", {"metriques": metriques_context})

    # Pour les scrapers automatisés Prometheus (machine-to-machine) : renvoyer le flux text/plain standard OpenMetrics
    return HttpResponse(contenu_metrics, content_type="text/plain; version=0.0.4; charset=utf-8")
