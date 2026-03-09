@echo off
REM Script rapide pour vérifier la collecte World Bank

cd /d "E:\DISQUE C\Desktop\Implementation plateforme"

echo.
echo ===================================
echo VERIFICATION COLLECTE WORLD BANK
echo ===================================
echo.

REM Activer l'environnement virtuel
call .venv\Scripts\activate.bat

REM Vérifier le progrès
python verifier_collecte_wb.py

echo.
echo Pour voir les logs de collecte :
echo    tail -50 collecte_wb_2025_2026.log
echo.

pause
