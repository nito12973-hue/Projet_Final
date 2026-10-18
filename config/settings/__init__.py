"""
Point d'entrée principal des réglages Django (SantéSN).
Sélectionne automatiquement l'environnement selon DJANGO_ENV ou DEBUG.
Garantit une configuration 'Secure-by-default' (production par défaut sauf en mode dev explicite).
"""
import os
import sys
from decouple import config

_env = os.environ.get('DJANGO_ENV', '').strip().lower()
_debug = str(config('DEBUG', default='False')).strip().lower() in {'1', 'true', 'yes', 'on'}
_is_cloud = bool(os.environ.get('VERCEL') or os.environ.get('RENDER') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))

if 'test' in sys.argv:
    from .dev import *
elif _env in {'dev', 'development', 'local'} or (_debug and _env != 'production' and not _is_cloud):
    from .dev import *
else:
    from .prod import *

