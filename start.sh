#!/bin/bash
# Script de démarrage du serveur Django

set -e

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "🚀 Démarrage de la Plateforme de Centralisation..."
echo ""

# Vérifier si l'environnement virtuel existe
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ L'environnement virtuel n'existe pas${NC}"
    echo "Exécutez d'abord: ./setup.sh"
    exit 1
fi

# Activer l'environnement virtuel
source .venv/Scripts/activate

# Vérifier la connexion MongoDB
echo "🗄️  Vérification de MongoDB..."
if python manage.py check --database default &> /dev/null; then
    echo -e "${GREEN}✓ MongoDB connecté${NC}"
else
    echo -e "${RED}❌ Impossible de se connecter à MongoDB${NC}"
    echo "Assurez-vous que MongoDB est démarré"
    exit 1
fi

# Appliquer les migrations si nécessaire
echo ""
echo "📋 Vérification des migrations..."
python manage.py migrate --check &> /dev/null || {
    echo "Application des migrations..."
    python manage.py migrate
}

# Collecter les fichiers statiques (si nécessaire)
if [ "$1" == "--prod" ]; then
    echo ""
    echo "📦 Collecte des fichiers statiques..."
    python manage.py collectstatic --noinput
fi

# Démarrer le serveur
echo ""
echo -e "${GREEN}✅ Démarrage du serveur Django...${NC}"
echo ""
echo -e "Dashboard: ${YELLOW}http://localhost:8000${NC}"
echo -e "Admin: ${YELLOW}http://localhost:8000/admin${NC}"
echo -e "API: ${YELLOW}http://localhost:8000/api/ingestion/health/${NC}"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter"
echo ""

# Démarrer avec le port spécifié ou par défaut
PORT="${2:-8000}"
python manage.py runserver "0.0.0.0:$PORT"
