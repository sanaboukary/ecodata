# Dockerfile pour Plateforme de Centralisation des Données Économiques
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="SANA Expert"
LABEL description="Plateforme de Centralisation des Données Économiques CEDEAO"
LABEL version="1.0"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=plateforme_centralisation.settings \
    TZ=Africa/Abidjan

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Créer le répertoire de l'application
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copier le code de l'application
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p staticfiles media logs airflow/logs

# Collecter les fichiers statiques
RUN python manage.py collectstatic --noinput || true

# Exposer les ports
EXPOSE 8000

# Script de démarrage
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "plateforme_centralisation.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
