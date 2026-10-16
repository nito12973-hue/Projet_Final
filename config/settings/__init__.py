"""
Point d'entrée principal des réglages Django (SantéSN).
Sélectionne automatiquement l'environnement (dev ou prod) selon DJANGO_ENV ou DEBUG.
Garantit une compatibilité totale avec DJANGO_SETTINGS_MODULE='config.settings'.
"""
import os
import sys
from decouple import config

_env = os.environ.get('DJANGO_ENV', '').strip().lower()
_debug = str(config('DEBUG', default='True')).strip().lower() in {'1', 'true', 'yes', 'on'}

if 'test' in sys.argv:
    from .dev import *
elif _env == 'production' or (_env == '' and not _debug):
    from .prod import *
else:
    from .dev import *
