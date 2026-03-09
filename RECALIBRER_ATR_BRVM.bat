@echo off
chcp 65001 > nul
cls

echo ================================================================================
echo RECALIBRATION ATR BRVM PRO - PRODUCTION DEFINITIVE
echo ================================================================================
echo.
echo Cette operation va recalculer tous les indicateurs WEEKLY avec:
echo   - ATR base sur 5 semaines (sweet spot BRVM)
echo   - Filtrage semaines mortes (volume=0, prix bloques)
echo   - Seuils realistes: 6-25%%
echo   - Stop/Target institutionnels (RR=2.6)
echo.
echo ================================================================================
echo.

python brvm_pipeline\pipeline_weekly.py --indicators

if %errorlevel% neq 0 (
    echo.
    echo ERREUR lors du recalcul
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo.
echo OK Recalibration ATR terminee avec succes
echo.
echo VALIDATION FINALE:
echo   - ATR moyen univers: doit etre 6-14%%
echo   - Max ATR: doit etre ^< 25%%
echo   - Aucun ATR ^> 40%%
echo.
echo Si vous voyez encore 500%% quelque part = calcul casse
echo.
echo ================================================================================
echo.

python verifier_etat_brvm.py

pause
