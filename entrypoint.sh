#!/bin/sh

# Arrête le script si une commande échoue
set -e

# Attente de la base de données MongoDB
echo "Attente de MongoDB..."
sleep 10

# Commandes de préparation Django
echo "Migration de la base de données..."
python manage.py migrate --no-input || true

echo "Collecte des fichiers statiques..."
python manage.py collectstatic --no-input --clear || true

echo "Création de l'utilisateur administrateur..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@plateforme.com', 'admin123')
    print('✅ Utilisateur admin créé')
else:
    print('ℹ️ Utilisateur admin existe déjà')
" || true

echo "Initialisation de la base de données BRVM..."
python manage.py ingest_source --source brvm || true

echo "Démarrage du serveur Gunicorn..."
exec gunicorn plateforme_centralisation.wsgi:application --bind 0.0.0.0:8003 --workers 3 --timeout 120
