"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
app = application

try:
    from django.core.management import call_command
    call_command('migrate', interactive=False)
    call_command('seed_demo')
except Exception as e:
    import logging
    logging.getLogger('django').warning(f"Erreur initialisation automatique WSGI: {e}")

