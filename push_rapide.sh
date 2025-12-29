#!/bin/bash
# Script ultra-rapide pour push avec message automatique
# Usage: ./push_rapide.sh

# Message automatique avec date/heure
TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
COMMIT_MESSAGE="Update: Modifications du $TIMESTAMP"

echo "🚀 Push rapide vers GitHub..."
echo "Message: $COMMIT_MESSAGE"
echo ""

git add .
git commit -m "$COMMIT_MESSAGE"
git push

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Push réussi !"
else
    echo ""
    echo "❌ Échec du push"
fi
