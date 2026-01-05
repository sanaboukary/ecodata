@echo off
REM Collecteur BRVM Ultra-Robuste - Lancement rapide
REM Double-clic pour collecter les données BRVM

echo ============================================================
echo COLLECTEUR BRVM ULTRA-ROBUSTE v2.0
echo Avec Selenium Avance integre
echo ============================================================
echo.

cd /d "%~dp0"

REM Vérifier et démarrer MongoDB si nécessaire
echo [1/4] Verification MongoDB...
docker ps | findstr "centralisation_db" >nul
if %ERRORLEVEL% NEQ 0 (
    echo MongoDB non actif, demarrage...
    docker start centralisation_db
    timeout /t 3 /nobreak >nul
    echo MongoDB demarre!
) else (
    echo MongoDB deja actif
)

echo.
echo [2/4] Activation environnement Python...
call .venv\Scripts\activate.bat

echo.
echo [3/4] Test des dependances...
python test_collecteur.py | findstr /C:"OK" /C:"PRET"

echo.
echo [4/4] Lancement collecteur...
echo.
echo ============================================================
echo Strategies disponibles:
echo   0. Selenium Avance (FR/EN + cookies + export CSV)
echo   1. BeautifulSoup (leger)
echo   2. Import CSV (auto)
echo   3. Saisie manuelle (guidee)
echo ============================================================
echo.

python collecteur_brvm_ultra_robuste.py

echo.
echo ============================================================
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ COLLECTE REUSSIE
    echo.
    echo Verifiez les donnees:
    echo   - MongoDB: python show_complete_data.py
    echo   - CSV exportes: dir out_brvm\*.csv
    echo.
) else (
    echo.
    echo ❌ ECHEC COLLECTE
    echo.
    echo Solutions:
    echo   1. Verifier MongoDB: docker ps
    echo   2. Installer dependances: installer_dependances_collecteur.bat
    echo   3. Tester: python test_collecteur.py
    echo.
)
echo ============================================================

pause
