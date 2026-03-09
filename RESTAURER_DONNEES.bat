@echo off
chcp 65001 >nul
cd /d "E:\DISQUE C\Desktop\Implementation plateforme"

echo ================================================================================
echo RESTAURATION DES DONNEES BRVM PERDUES
echo ================================================================================
echo.
echo Ce script va restaurer 43 jours de donnees BRVM depuis curated_observations
echo vers prices_daily.
echo.
echo Donnees concernees:
echo   - Octobre 2025: 16 jours (16-31)
echo   - Novembre 2025: 20 jours (3-28)
echo   - Decembre 2025: 5 jours
echo   - Janvier 2026: 2 jours
echo   - Fevrier 2026: 1 jour
echo.
echo TOTAL: 43 jours de donnees recuperables
echo.
echo ================================================================================
echo.

"E:\DISQUE C\Desktop\Implementation plateforme\.venv\Scripts\python.exe" RESTAURER_DONNEES_FINAL.py

echo.
echo ================================================================================
echo.
echo Consulter RESTAURATION_BRVM_RESULTS.txt pour details
echo.
pause
