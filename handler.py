import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django
from django.core.wsgi import get_wsgi_application
django_app = get_wsgi_application()

# Vercel serverless handler
def handler(event, context):
    return django_app(event, context)
