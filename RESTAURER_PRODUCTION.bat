@echo off
chcp 65001 >nul
cd /d "E:\DISQUE C\Desktop\Implementation plateforme"

echo ================================================================================
echo RESTAURATION PRODUCTION - DONNEES BRVM
echo ================================================================================
echo.
echo Cette operation va :
echo   1. Identifier les jours manquants dans prices_daily
echo   2. Extraire depuis curated_observations (BRVM_AGGREGATED prioritaire)
echo   3. Valider qualite (OHLC coherent, prix realistes)
echo   4. Inserer proprement (upsert - pas de suppression)
echo.
echo OBJECTIF: ~69 jours de donnees pour 14+ semaines WEEKLY
echo.
echo ================================================================================
echo.

call .venv\Scripts\activate.bat
python restauration_brvm_production.py

echo.
echo ================================================================================
echo.
if %ERRORLEVEL% EQU 0 (
    echo OK Restauration terminee avec succes
    echo.
    echo PROCHAINES ETAPES OBLIGATOIRES:
    echo   1. python brvm_pipeline/pipeline_weekly.py --rebuild
    echo   2. python brvm_pipeline/pipeline_weekly.py --indicators
    echo.
) else (
    echo ERREUR lors de la restauration
    echo Consulter les messages ci-dessus
    echo.
)

pause
