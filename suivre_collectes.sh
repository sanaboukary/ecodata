#!/bin/bash
# Suivi des collectes internationales en cours

clear
echo "=================================="
echo "SUIVI COLLECTES INTERNATIONALES"
echo "=================================="
echo ""
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Verifier les processus
echo "--- PROCESSUS ACTIFS ---"
ps aux | grep -E "collecter_(worldbank|imf|afdb)" | grep -v grep | awk '{print $2, $11}' || echo "Aucun processus actif"
echo ""

# Stats des fichiers log
echo "--- FICHIERS LOG ---"
for log in wb_1990_2026.log imf_1990_2026.log afdb_un_1990_2026.log; do
    if [ -f "$log" ]; then
        size=$(du -h "$log" | cut -f1)
        lines=$(wc -l < "$log")
        echo "$log: $size ($lines lignes)"
    fi
done
echo ""

# Progression World Bank
if [ -f "wb_1990_2026.log" ]; then
    echo "--- WORLD BANK ---"
    wb_done=$(grep -c "OK -" wb_1990_2026.log 2>/dev/null || echo 0)
    wb_fail=$(grep -c "ECHEC" wb_1990_2026.log 2>/dev/null || echo 0)
    echo "Operations: $wb_done reussies, $wb_fail echouees / 88 total"
    
    if grep -q "RAPPORT FINAL" wb_1990_2026.log 2>/dev/null; then
        echo "Status: TERMINE"
        grep "Total observations:" wb_1990_2026.log | tail -1
    else
        echo "Status: EN COURS"
        tail -3 wb_1990_2026.log 2>/dev/null | head -2
    fi
fi
echo ""

# Progression IMF
if [ -f "imf_1990_2026.log" ]; then
    echo "--- IMF ---"
    imf_done=$(grep -c "OK -" imf_1990_2026.log 2>/dev/null || echo 0)
    imf_fail=$(grep -c "ECHEC" imf_1990_2026.log 2>/dev/null || echo 0)
    echo "Operations: $imf_done reussies, $imf_fail echouees / 64 total"
    
    if grep -q "RAPPORT FINAL" imf_1990_2026.log 2>/dev/null; then
        echo "Status: TERMINE"
        grep "Total observations:" imf_1990_2026.log | tail -1
    else
        echo "Status: EN COURS"
        tail -3 imf_1990_2026.log 2>/dev/null | head -2
    fi
fi
echo ""

# Progression AfDB + UN
if [ -f "afdb_un_1990_2026.log" ]; then
    echo "--- AfDB + UN SDG ---"
    afdb_done=$(grep -c "OK -" afdb_un_1990_2026.log 2>/dev/null || echo 0)
    afdb_fail=$(grep -c "ECHEC" afdb_un_1990_2026.log 2>/dev/null || echo 0)
    echo "Operations: $afdb_done reussies, $afdb_fail echouees / 96 total"
    
    if grep -q "RAPPORT FINAL" afdb_un_1990_2026.log 2>/dev/null; then
        echo "Status: TERMINE"
        tail -10 afdb_un_1990_2026.log | grep "Observations:"
    else
        echo "Status: EN COURS"
        tail -3 afdb_un_1990_2026.log 2>/dev/null | head -2
    fi
fi
echo ""

echo "=================================="
echo "Commandes utiles:"
echo "  tail -f wb_1990_2026.log"
echo "  tail -f imf_1990_2026.log"
echo "  tail -f afdb_un_1990_2026.log"
echo "  python resume_simple.py"
echo "=================================="
