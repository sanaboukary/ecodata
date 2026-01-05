@echo off
REM Collecte COMPLÈTE BRVM - 47 Actions avec toutes métriques

echo ============================================================
echo COLLECTEUR COMPLET BRVM - 47 ACTIONS
echo ============================================================
echo.
echo Metriques collectees:
echo   • Cours (prix)
echo   • Variations (pourcentage)
echo   • Volatilite (30 jours)
echo   • Liquidite (volume moyen)
echo   • OHLC complet
echo   • Volume, Valeur, Transactions
echo   • Capitalisation
echo.
echo ============================================================
echo.

cd /d "%~dp0"

REM MongoDB
echo [1/3] Verification MongoDB...
docker ps | findstr "centralisation_db" >nul
if %ERRORLEVEL% NEQ 0 (
    echo Demarrage MongoDB...
    docker start centralisation_db
    timeout /t 3 /nobreak >nul
)
echo MongoDB: OK

echo.
echo [2/3] Activation Python...
call .venv\Scripts\activate.bat

echo.
echo [3/3] Lancement collecte...
echo.

python collecter_brvm_complet.py

echo.
echo ============================================================
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ COLLECTE REUSSIE
    echo.
    echo Verifier les donnees:
    echo   MongoDB: python -c "from pymongo import MongoClient; ..."
    echo   CSV: dir out_brvm\brvm_complet_*.csv
    echo.
) else (
    echo.
    echo ❌ ECHEC - Verifier les logs ci-dessus
    echo.
)
echo ============================================================

pause
