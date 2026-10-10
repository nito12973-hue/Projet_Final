#!/bin/sh
set -e

echo "=== Initialisation de SantéSN Production ==="

# Attente de la disponibilité de la base de données PostgreSQL si configurée
if [ -n "$DB_HOST" ]; then
    echo "Attente de la base de données sur $DB_HOST:${DB_PORT:-5432}..."
    while ! nc -z "$DB_HOST" "${DB_PORT:-5432}"; do
        sleep 0.5
    done
    echo "Base de données accessible !"
fi

# Application automatique des migrations
echo "Application des migrations de base de données..."
python manage.py migrate --noinput

# Collecte des fichiers statiques
echo "Collecte des fichiers statiques (WhiteNoise)..."
python manage.py collectstatic --noinput --clear || true

echo "SantéSN prêt pour le démarrage."
exec "$@"
