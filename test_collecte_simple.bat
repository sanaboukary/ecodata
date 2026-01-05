@echo off
REM Test rapide du script de collecte simplifié

echo ============================================================
echo TEST COLLECTE BRVM SIMPLIFIEE
echo ============================================================
echo.

cd /d "%~dp0"

echo Activation environnement virtuel...
call .venv\Scripts\activate.bat

echo.
echo Test 1: Verification des donnees existantes (--check)
echo ------------------------------------------------------------
python collecte_brvm_simple.py --check

echo.
echo.
echo Test 2: Tentative de collecte
echo ------------------------------------------------------------
python collecte_brvm_simple.py

echo.
echo ============================================================
echo TEST TERMINE
echo ============================================================
pause
