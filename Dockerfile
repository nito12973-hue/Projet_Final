# =============================================================================
# SantéSN — Image Docker de Production Industrielle
# =============================================================================

# Étape 1 : Construction et installation des dépendances
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dépendances système de compilation pour PostgreSQL et ReportLab
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# Étape 2 : Image finale d'exécution (légère et durcie)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Dépendances système d'exécution (bibliothèques dynamiques uniquement)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    zlib1g \
    libfreetype6 \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie des packages Python pré-compilés
COPY --from=builder /install /usr/local

# Création d'un utilisateur applicatif non-privilégié (Sécurité OWASP)
RUN groupadd -r santesn && useradd -r -g santesn -d /app -s /bin/bash santesn

# Copie du code source
COPY . .

# Création des dossiers statiques et médias avec permissions
RUN mkdir -p /app/staticfiles /app/media /app/logs && \
    chown -R santesn:santesn /app && \
    chmod +x /app/docker-entrypoint.sh

USER santesn

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "2", "--timeout", "60"]
