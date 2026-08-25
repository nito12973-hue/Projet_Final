web: python manage.py migrate --no-input && python manage.py seed_demo && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT

