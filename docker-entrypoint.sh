#!/bin/bash
set -e

echo "🚀 Démarrage de la Plateforme de Centralisation..."

# Attendre que MongoDB soit prêt
echo "⏳ Attente de MongoDB..."
until mongosh "$MONGODB_URI" --eval "db.adminCommand('ping')" > /dev/null 2>&1; do
  sleep 2
done
echo "✅ MongoDB est prêt!"

# Exécuter les migrations Django
echo "📦 Exécution des migrations..."
python manage.py migrate --noinput || echo "⚠️ Migrations échouées, continuons..."

# Créer un superutilisateur si nécessaire
echo "👤 Vérification du superutilisateur..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@plateforme.local', 'admin123')
    print('✅ Superutilisateur créé: admin/admin123')
else:
    print('✅ Superutilisateur existe déjà')
" || echo "⚠️ Création superutilisateur échouée"

# Collecter les fichiers statiques
echo "📂 Collection des fichiers statiques..."
python manage.py collectstatic --noinput || echo "⚠️ Collection des fichiers statiques échouée"

echo "✅ Initialisation terminée!"

# Exécuter la commande fournie
exec "$@"
