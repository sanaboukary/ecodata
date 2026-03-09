@echo off
REM Collecte World Bank optimisee en arriere-plan

cd /d "E:\DISQUE C\Desktop\Implementation plateforme"

echo.
echo ================================================
echo  COLLECTE WORLD BANK OPTIMISEE (1960-2026)
echo ================================================
echo.
echo Operations: 3,696 (reduction 90%%)
echo Duree estimee: ~2 heures
echo.

call .venv\Scripts\activate.bat

echo Demarrage de la collecte...
start /B python collecter_wb_optimise.py > collecte_wb_bg.log 2>&1

echo.
echo Collecte lancee en arriere-plan
echo Logs: collecte_wb_bg.log
echo.
echo Pour suivre le progres:
echo    python moniteur_collecte.py
echo.

pause
