"""
Paramètres communs et socle de configuration pour SantéSN.
Partagé entre les environnements de développement, test et production.
"""
import os
import sys
from pathlib import Path
from decouple import Csv, config

# Build paths inside the project: BASE_DIR / 'subdir'
# base.py est dans config/settings/, donc parent x 3 remonte à la racine du projet
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Clé secrète par défaut pour le développement
DEFAULT_SECRET_KEY = 'django-insecure-santesn-platform-cloud-default-key-2026-prod-secure-dakar'
_raw_secret_key = config('SECRET_KEY', default=DEFAULT_SECRET_KEY)
if not _raw_secret_key or not str(_raw_secret_key).strip():
    _raw_secret_key = DEFAULT_SECRET_KEY
SECRET_KEY = str(_raw_secret_key).strip()

# Détection de l'URL publique
SITE_URL = str(config(
    'SITE_URL',
    default='https://projet-final-bice.vercel.app',
) or '').strip().rstrip('/').strip()

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'Plateform_medicale.apps.PlateformMedicaleConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'Plateform_medicale.views.user_role',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Validation des mots de passe
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalisation & Fuseau horaire (Sénégal)
LANGUAGE_CODE = 'fr'
TIME_ZONE = 'Africa/Dakar'
USE_I18N = True
USE_TZ = True

# Fichiers statiques et stockage
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    "default": {
        "BACKEND": "Plateform_medicale.storage.DatabaseMediaStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Fichiers médias (téléversements)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Modèle utilisateur personnalisé & redirections d'authentification
AUTH_USER_MODEL = 'Plateform_medicale.User'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'post_login_redirect'
LOGOUT_REDIRECT_URL = 'login'

# Sessions
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 60 * 60 * 8  # 8 heures
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True

# Messagerie transactionnelle (Email SMTP)
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='lamaranamamadousdiallo@gmail.com')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='yinprgglnfbmxxut')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='lamaranamamadousdiallo@gmail.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Notification WhatsApp Business
WHATSAPP_ENABLED = config('WHATSAPP_ENABLED', default=True, cast=bool)
WHATSAPP_API_TOKEN = config(
    'WHATSAPP_API_TOKEN',
    default='EAAXGE8OjzPIBSob502MA3fYZATbQgOZCXhykrgxUiF51ItqwCApwGsXhH9OAp2kBmGKK8VlHVw6WpoSEK0Xp44EOGVZCgprnV0UjZBO4iMdFL1BqycKtGDhDw8ZBG8V6ZB14CM1J5VZCZBOUlQY4r0csF1WK7piPqlHEjD46laq1HPkLhhP9i4qbr365XZAdYWnhqFgZDZD',
)
WHATSAPP_PHONE_NUMBER_ID = config('WHATSAPP_PHONE_NUMBER_ID', default='1372241212628957')
WHATSAPP_TEMPLATE_NAME = config('WHATSAPP_TEMPLATE_NAME', default=None)
WHATSAPP_SENDER_PHONE = config('WHATSAPP_SENDER_PHONE', default='221789576145')
WHATSAPP_WEBHOOK_VERIFY_TOKEN = config('WHATSAPP_WEBHOOK_VERIFY_TOKEN', default='santesn_webhook_secret_2026')

if 'test' in sys.argv:
    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    WHATSAPP_ENABLED = False

# Règles métier de l'assurance santé (Sénégal)
DELAI_VALIDITE_ORDONNANCE_JOURS = config('DELAI_VALIDITE_ORDONNANCE_JOURS', default=90, cast=int)
ORDONNANCE_SCEAU_CLE = config('ORDONNANCE_SCEAU_CLE', default='')
MAX_AYANTS_DROIT_PAR_ASSURE = config('MAX_AYANTS_DROIT_PAR_ASSURE', default=6, cast=int)
MAX_CONJOINTS_PAR_ASSURE = config('MAX_CONJOINTS_PAR_ASSURE', default=4, cast=int)
MAX_ENFANTS_PAR_ASSURE = config('MAX_ENFANTS_PAR_ASSURE', default=6, cast=int)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SENTRY_DSN = config('SENTRY_DSN', default=None)

# Base de données et hashers pour les tests automatisés : isolation absolue
if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
    PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
