@echo off
chcp 65001 > nul
cls

echo ================================================================================
echo REBUILD WEEKLY COMPLET - ATR BRVM PRO
echo ================================================================================
echo.
echo Cette operation va:
echo   1. SUPPRIMER toutes les semaines weekly actuelles (88.5%% volume=0)
echo   2. REBUILD depuis prices_daily (100%% OHLC complet, 72 jours)
echo   3. CALCULER indicateurs avec ATR BRVM PRO:
echo      - Filtre semaines mortes (volume=0, prix bloques)
echo      - ATR sur 5 semaines (sweet spot BRVM)
echo      - Seuils realistes: 6-25%%
echo      - Stop/Target institutionnels (RR=2.6)
echo.
echo Attendez environ 60-90 secondes...
echo.
echo ================================================================================
echo.

.venv\Scripts\python.exe brvm_pipeline\pipeline_weekly.py --rebuild

if %errorlevel% neq 0 (
    echo.
    echo ERREUR lors du rebuild
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo.
echo OK Rebuild termine avec succes
echo.
echo VALIDATION:
echo   - ATR moyen doit etre 6-14%%
echo   - Max ATR doit etre ^< 25%%
echo   - Aucun ATR ^> 40%%
echo   - Actions tradables: 20-40%%
echo.
echo ================================================================================
echo.

.venv\Scripts\python.exe verifier_etat_brvm.py

pause
