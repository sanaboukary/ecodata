@echo off
REM Script batch pour lancer la collecte quotidienne BRVM
echo ================================================================================
echo COLLECTE QUOTIDIENNE BRVM - DONNEES REELLES UNIQUEMENT
echo ================================================================================

cd "E:\DISQUE C\Desktop\Implementation plateforme"

REM Activer l'environnement virtuel
call .venv\Scripts\activate.bat

REM Lancer la collecte via manage.py
python manage.py ingest_source --source brvm

echo.
echo ================================================================================
echo Collecte terminee
echo ================================================================================
pause
