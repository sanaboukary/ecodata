#!/bin/bash
# Suivi de la collecte World Bank

echo "=================================="
echo "SUIVI COLLECTE WORLD BANK"
echo "=================================="
echo ""

# Trouver le dernier fichier log
LOGFILE=$(ls -t collecte_wb_complete_*.log 2>/dev/null | head -1)

if [ -z "$LOGFILE" ]; then
    echo "Aucun fichier log trouve"
    exit 1
fi

echo "Fichier log: $LOGFILE"
echo "Taille: $(du -h "$LOGFILE" | cut -f1)"
echo ""

# Afficher progression
echo "--- PROGRESSION ---"
grep -E "\[.*\] (Benin|Burkina|Cote|Guinee|Mali|Niger|Senegal|Togo)" "$LOGFILE" | tail -10
echo ""

# Afficher statistiques si disponibles
if grep -q "RAPPORT FINAL" "$LOGFILE"; then
    echo "--- COLLECTE TERMINEE ---"
    grep -A 20 "RAPPORT FINAL" "$LOGFILE"
else
    echo "Collecte en cours..."
    
    # Compter operations terminees
    DONE=$(grep -c "OK -" "$LOGFILE" 2>/dev/null || echo 0)
    FAILED=$(grep -c "ECHEC" "$LOGFILE" 2>/dev/null || echo 0)
    TOTAL=88
    
    echo "Operations terminees: $DONE/$TOTAL"
    echo "Echecs: $FAILED"
fi

echo ""
echo "Pour voir le log complet: cat $LOGFILE"
