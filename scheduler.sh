#!/bin/bash
# Script de démarrage du scheduler BRVM

set -e

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "⏰ Démarrage du Scheduler BRVM..."
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
    exit 1
fi

# Démarrer le scheduler
echo ""
echo -e "${GREEN}✅ Démarrage du scheduler BRVM (horaire)...${NC}"
echo ""
echo "Le scheduler va récupérer les données BRVM toutes les heures"
echo "Logs: logs/scheduler.log"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter"
echo ""

# Créer le dossier logs s'il n'existe pas
mkdir -p logs

# Démarrer avec logging
python manage.py start_scheduler 2>&1 | tee logs/scheduler.log
