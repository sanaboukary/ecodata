#!/bin/bash
# Script pour exécuter les tests

set -e

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "🧪 Exécution des tests..."
echo ""

# Activer l'environnement virtuel
if [ -d ".venv" ]; then
    source .venv/Scripts/activate
else
    echo -e "${RED}❌ L'environnement virtuel n'existe pas${NC}"
    exit 1
fi

# Options
COVERAGE=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            APP=$1
            shift
            ;;
    esac
done

# Exécuter les tests avec ou sans couverture
if [ "$COVERAGE" = true ]; then
    echo "📊 Exécution avec couverture de code..."
    if [ -z "$APP" ]; then
        coverage run --source='.' manage.py test
    else
        coverage run --source='.' manage.py test $APP
    fi
    echo ""
    coverage report
    echo ""
    echo "Rapport HTML généré dans htmlcov/index.html"
    coverage html
else
    if [ "$VERBOSE" = true ]; then
        VERBOSITY=2
    else
        VERBOSITY=1
    fi
    
    if [ -z "$APP" ]; then
        python manage.py test --verbosity=$VERBOSITY
    else
        python manage.py test $APP --verbosity=$VERBOSITY
    fi
fi

echo ""
echo -e "${GREEN}✅ Tests terminés${NC}"
