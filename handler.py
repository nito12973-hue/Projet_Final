import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django
from django.core.wsgi import get_wsgi_application

# Vercel expects the WSGI app to be named 'app' or 'application'
app = get_wsgi_application()
