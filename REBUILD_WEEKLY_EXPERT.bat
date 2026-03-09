@echo off
chcp 65001 > nul
cls

echo ================================================================================
echo REBUILD WEEKLY COMPLET - MODE EXPERT BRVM
echo ================================================================================
echo.
echo Cette operation va:
echo   1. Supprimer toutes les semaines weekly actuelles (donnees cassees)
echo   2. Rebuild complet depuis 72 jours de prices_daily
echo   3. Recalculer indicateurs avec ATR BRVM PRO
echo   4. Tester moteur WEEKLY EXPERT
echo.
echo ================================================================================
echo.

echo ETAPE 1/3: Rebuild WEEKLY complet...
.venv\Scripts\python.exe brvm_pipeline\pipeline_weekly.py --rebuild

if %errorlevel% neq 0 (
    echo ERREUR lors du rebuild
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo ETAPE 2/3: Verification ATR...
.venv\Scripts\python.exe verif_atr_simple.py

echo.
echo ================================================================================
echo ETAPE 3/3: Test moteur EXPERT BRVM...
.venv\Scripts\python.exe brvm_pipeline\weekly_engine_expert.py --week 2026-W07

echo.
echo ================================================================================
echo TERMINE
echo ================================================================================
pause
