"""
Configuration de production sécurisée pour SantéSN (Docker & Cloud PaaS).
Applique les standards de sécurité bancaire et médicale (Loi 2008-12 CDP).
"""
import os
import sys
from django.core.exceptions import ImproperlyConfigured
from .base import *

DEBUG = False

# Vérification obligatoire de la clé secrète en production
if SECRET_KEY == DEFAULT_SECRET_KEY:
    raise ImproperlyConfigured(
        "En production (DEBUG=False), une clé secrète SECRET_KEY unique et robuste doit être définie dans l'environnement."
    )

_allowed_hosts_config = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,projet-final-bice.vercel.app,projet-final.vercel.app,santesn.sn,www.santesn.sn,.santesn.sn',
    cast=Csv(),
)
ALLOWED_HOSTS = list(_allowed_hosts_config)
for host in [
    'projet-final-bice.vercel.app',
    'projet-final.vercel.app',
    'santesn.sn',
    'www.santesn.sn',
    '.santesn.sn',
    'localhost',
    '127.0.0.1',
]:
    if host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(host)

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

CSRF_TRUSTED_ORIGINS = [
    'https://projet-final-bice.vercel.app',
    'https://projet-final.vercel.app',
    'https://santesn.sn',
    'https://www.santesn.sn',
    'https://*.santesn.sn',
]
for _origin in config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv()):
    if _origin and _origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_origin)

# Base de données PostgreSQL obligatoire en production (hors tests automatisés)
if 'test' not in sys.argv:
    DATABASE_URL = os.environ.get('DATABASE_URL') or config('DATABASE_URL', default=None)
    if DATABASE_URL and str(DATABASE_URL).strip().startswith(('postgres://', 'postgresql://')):
        import dj_database_url
        DATABASES = {
            'default': dj_database_url.parse(
                str(DATABASE_URL).strip(),
                conn_max_age=600,
                conn_health_checks=True,
                ssl_require=True,
            )
        }
        DATABASES['default']['DISABLE_SERVER_SIDE_CURSORS'] = True
    elif os.environ.get('VERCEL') or os.environ.get('RENDER'):
        raise ImproperlyConfigured("DATABASE_URL est obligatoire en environnement de production (Vercel/Render).")
    elif config('DB_ENGINE', default='sqlite') == 'postgresql':
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': config('DB_NAME'),
                'USER': config('DB_USER'),
                'PASSWORD': config('DB_PASSWORD'),
                'HOST': config('DB_HOST', default='localhost'),
                'PORT': config('DB_PORT', default='5432'),
                'CONN_MAX_AGE': 60,
                'CONN_HEALTH_CHECKS': True,
            }
        }
    else:
        raise ImproperlyConfigured("Une base de données PostgreSQL est requise pour la production SantéSN.")

# Offloading Nginx pour les médias protégés
USE_X_ACCEL_REDIRECT = True

# Durcissement HTTPS & Cookies sécurisés
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = 'same-origin'

if SECURE_SSL_REDIRECT:
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
    SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)

# Logging de production
LOGS_DIR = BASE_DIR / 'logs'
CAN_WRITE_LOGS = False
try:
    LOGS_DIR.mkdir(exist_ok=True)
    if not os.environ.get('VERCEL'):
        _test_log = LOGS_DIR / 'django.log'
        with open(_test_log, 'a', encoding='utf-8'):
            pass
        CAN_WRITE_LOGS = True
except OSError:
    CAN_WRITE_LOGS = False

_LOG_HANDLERS = ['console', 'file'] if CAN_WRITE_LOGS else ['console']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        **(
            {
                'file': {
                    'class': 'logging.FileHandler',
                    'filename': LOGS_DIR / 'django.log',
                    'formatter': 'verbose',
                    'level': 'WARNING',
                    'encoding': 'utf-8',
                }
            }
            if CAN_WRITE_LOGS
            else {}
        ),
    },
    'loggers': {
        'django': {
            'handlers': _LOG_HANDLERS,
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': _LOG_HANDLERS,
            'level': 'ERROR',
            'propagate': False,
        },
        'Plateform_medicale': {
            'handlers': _LOG_HANDLERS,
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Observabilité Sentry
SENTRY_DSN = config('SENTRY_DSN', default=None)
if SENTRY_DSN and 'test' not in sys.argv:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration

        def _filtrer_donnees_santesn(event, hint):
            if 'request' in event and 'data' in event['request']:
                data = event['request']['data']
                if isinstance(data, dict):
                    champs_sensibles = {'password', 'mot_de_passe', 'numero_securite_sociale', 'cle_secours', 'ordonnance'}
                    for cle in champs_sensibles:
                        if cle in data:
                            data[cle] = '[MASQUÉ_SANTESN]'
            return event

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            traces_sample_rate=0.2,
            send_default_pii=False,
            before_send=_filtrer_donnees_santesn,
            environment='production',
        )
    except Exception:
        pass
