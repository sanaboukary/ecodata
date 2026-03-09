@echo off
REM ========================================
REM WORKFLOW COMPLET BRVM
REM Generer recommandations hebdomadaires
REM ========================================

echo.
echo ========================================
echo  WORKFLOW BRVM - RECOMMANDATIONS
echo ========================================
echo.

cd /d "%~dp0"

REM Activer environnement virtuel
call .venv\Scripts\activate.bat

REM 1. Analyser actions BRVM
echo [1/2] Analyse technique actions BRVM...
python analyse_ia_simple.py

REM 2. Generer recommandations + dashboard
echo.
echo [2/2] Generation recommandations TOP5...
python workflow_production_django.py

REM Afficher dashboard
echo.
echo ========================================
echo  RECOMMANDATIONS DISPONIBLES
echo ========================================
type dashboard_output.txt

echo.
echo ========================================
echo  TERMINE !
echo ========================================
echo.
pause
