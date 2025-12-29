#!/bin/bash
# Script de configuration initiale du projet

set -e  # Arrêter en cas d'erreur

echo "🚀 Configuration de la Plateforme de Centralisation..."
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Vérifier Python
echo "📦 Vérification de Python..."
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python n'est pas installé${NC}"
    exit 1
fi

PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python $PYTHON_VERSION trouvé${NC}"

# Vérifier MongoDB
echo ""
echo "🗄️  Vérification de MongoDB..."
if ! command -v mongo &> /dev/null && ! command -v mongod &> /dev/null; then
    echo -e "${YELLOW}⚠️  MongoDB n'est pas détecté. Assurez-vous qu'il est installé et démarré.${NC}"
else
    echo -e "${GREEN}✓ MongoDB trouvé${NC}"
fi

# Créer l'environnement virtuel
echo ""
echo "🔧 Création de l'environnement virtuel..."
if [ ! -d ".venv" ]; then
    python -m venv .venv
    echo -e "${GREEN}✓ Environnement virtuel créé${NC}"
else
    echo -e "${YELLOW}⚠️  L'environnement virtuel existe déjà${NC}"
fi

# Activer l'environnement virtuel
echo ""
echo "🔌 Activation de l'environnement virtuel..."
source .venv/Scripts/activate

# Mettre à jour pip
echo ""
echo "📥 Mise à jour de pip..."
python -m pip install --upgrade pip --quiet

# Installer les dépendances
echo ""
echo "📦 Installation des dépendances..."
if [ "$1" == "--dev" ]; then
    echo "Mode développement activé"
    pip install -r requirements/dev.txt --quiet
else
    pip install -r requirements/base.txt --quiet
fi
echo -e "${GREEN}✓ Dépendances installées${NC}"

# Créer le fichier .env s'il n'existe pas
echo ""
echo "⚙️  Configuration de l'environnement..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    
    # Générer une clé secrète Django
    SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    
    # Remplacer la clé secrète dans .env (compatible avec sed sur Windows Git Bash)
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        sed -i "s/DJANGO_SECRET_KEY=change-me-in-production/DJANGO_SECRET_KEY=$SECRET_KEY/" .env
    else
        sed -i "" "s/DJANGO_SECRET_KEY=change-me-in-production/DJANGO_SECRET_KEY=$SECRET_KEY/" .env
    fi
    
    echo -e "${GREEN}✓ Fichier .env créé avec une clé secrète unique${NC}"
else
    echo -e "${YELLOW}⚠️  Le fichier .env existe déjà${NC}"
fi

# Vérifier la configuration Django
echo ""
echo "🔍 Vérification de la configuration Django..."
python manage.py check

# Créer les migrations
echo ""
echo "📋 Application des migrations..."
python manage.py migrate

echo ""
echo -e "${GREEN}✅ Configuration terminée avec succès !${NC}"
echo ""
echo "Pour démarrer le serveur :"
echo -e "${YELLOW}  source .venv/Scripts/activate${NC}"
echo -e "${YELLOW}  python manage.py runserver${NC}"
echo ""
echo "Ou utilisez le script de démarrage :"
echo -e "${YELLOW}  ./start.sh${NC}"
