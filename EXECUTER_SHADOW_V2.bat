@echo off
REM ====================================================
REM EXECUTION SHADOW DEPLOYMENT - V1 vs V2
REM ====================================================
REM
REM Ce script execute:
REM 1. ALPHA v2 (hebdomadaire, 4 facteurs)
REM 2. Affichage TOP 10 v2
REM
REM Impact clients: AUCUN (v1 reste production)
REM ====================================================

echo.
echo ================================================================================
echo SHADOW DEPLOYMENT - ALPHA SCORE V2 HEBDOMADAIRE
echo ================================================================================
echo.
echo Execution v2 (shadow mode - formule 4 facteurs)...
echo.

.venv\Scripts\python.exe alpha_v2_weekly_nodj.py

echo.
echo ================================================================================
echo TOP 10 ALPHA V2 vs V1
echo ================================================================================
echo.

.venv\Scripts\python.exe afficher_top10_v2.py

.venv\Scripts\python.exe afficher_top10_v2.py

echo.
echo ================================================================================
echo SHADOW DEPLOYMENT TERMINE
echo ================================================================================
echo.
echo Formule V2: 35%% EM + 25%% VS + 20%% Event + 20%% Sentiment
echo.
echo Prochaine execution: Lundi prochain (tracking hebdomadaire sur 4 semaines)
echo.
echo Donnees sauvegardees:
echo   - MongoDB collection: curated_observations
echo   - Dataset: ALPHA_V2_SHADOW
echo.
echo Production clients: INCHANGEE (v1 actif)
echo.

pause
