@echo off
cd /d "e:\DISQUE C\Desktop\Implementation plateforme"

echo ======================================================================
echo ANALYSE FORCEE AVEC RECHARGEMENT MODULE
echo ======================================================================
echo.

echo Etape 1: Cleanup cache Python...
del /S /Q __pycache__ >nul 2>&1
del /S /Q *.pyc >nul 2>&1
echo [OK] Cache nettoye

echo.
echo Etape 2: Analyse semantique avec module fresh...
.venv\Scripts\python.exe analyse_force_reload.py

echo.
echo Etape 3: Check resultats...
.venv\Scripts\python.exe check_final_results.py
type resultats_finaux.txt

echo.
echo ======================================================================
echo TERMINE!
echo ======================================================================
pause
