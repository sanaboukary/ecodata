@echo off
REM Collecte complète BRVM pour Analyse IA
REM Collecte: Prix, Variations, Volatilité, Liquidité - 47 actions

echo ============================================================
echo COLLECTEUR COMPLET BRVM - ANALYSE IA
echo ============================================================
echo.
echo Metriques collectees:
echo   - Prix (ouverture, cloture, haut, bas)
echo   - Variations (absolue, pourcentage)
echo   - Volatilite (5j, 20j, 60j)
echo   - Liquidite (volume, valeur, score)
echo.
echo Pour 47 actions BRVM
echo ============================================================
echo.

cd /d "%~dp0"

REM Démarrer MongoDB
echo [1/3] Verification MongoDB...
docker ps | findstr "centralisation_db" >nul
if %ERRORLEVEL% NEQ 0 (
    echo Demarrage MongoDB...
    docker start centralisation_db
    timeout /t 3 /nobreak >nul
)

echo.
echo [2/3] Activation Python...
call .venv\Scripts\activate.bat

echo.
echo [3/3] Collecte en cours...
echo ============================================================
echo.

python collecter_brvm_complet_ia.py

echo.
echo ============================================================
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ COLLECTE REUSSIE
    echo.
    echo Donnees disponibles dans:
    echo   - MongoDB: curated_observations
    echo   - CSV: out_brvm_ia\brvm_complete_ia_*.csv
    echo   - CSV ML: out_brvm_ia\brvm_ml_*.csv
    echo.
    echo Lancez votre analyse IA!
    echo.
) else (
    echo.
    echo ❌ ECHEC COLLECTE
    echo.
)
echo ============================================================

pause
