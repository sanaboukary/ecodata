#!/bin/bash
# Script automatique pour pousser les modifications vers GitHub
# Usage: ./push_github.sh "Votre message de commit"

# Couleurs pour l'affichage
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Push automatique vers GitHub${NC}"
echo "=============================================="

# Vérifier si un message de commit est fourni
if [ -z "$1" ]; then
    echo -e "${YELLOW}⚠️  Aucun message de commit fourni${NC}"
    echo -e "${YELLOW}📝 Veuillez décrire vos modifications :${NC}"
    read -p "> " COMMIT_MESSAGE
else
    COMMIT_MESSAGE="$1"
fi

# Vérifier qu'on a un message
if [ -z "$COMMIT_MESSAGE" ]; then
    echo -e "${RED}❌ Message de commit vide. Annulation.${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}📊 État actuel :${NC}"
git status --short

echo ""
echo -e "${BLUE}➕ Ajout des fichiers modifiés...${NC}"
git add .

echo ""
echo -e "${BLUE}💾 Création du commit...${NC}"
git commit -m "$COMMIT_MESSAGE"

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Aucune modification à commiter ou erreur de commit${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}🌐 Push vers GitHub...${NC}"
git push

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Code poussé avec succès vers GitHub !${NC}"
    echo -e "${GREEN}🔗 https://github.com/sanaboukary/ecodata${NC}"
else
    echo ""
    echo -e "${RED}❌ Erreur lors du push${NC}"
    exit 1
fi

echo ""
echo "=============================================="
