@echo off
REM Demarrage Airflow en arriere-plan (scheduler + webserver)
REM Pour Windows avec Git Bash

echo ============================================================
echo DEMARRAGE AIRFLOW - Mode Background
echo ============================================================

cd /d "%~dp0"

REM Activer l'environnement virtuel
call .venv\Scripts\activate.bat

REM Definir les variables d'environnement Airflow
set AIRFLOW_HOME=%CD%\airflow
set DJANGO_SETTINGS_MODULE=plateforme_centralisation.settings

echo.
echo Environnement Airflow: %AIRFLOW_HOME%
echo.

REM Demarrer le scheduler en arriere-plan
echo [1/2] Demarrage Airflow Scheduler...
start "Airflow Scheduler" /MIN cmd /c "call .venv\Scripts\activate.bat && airflow scheduler >> airflow\logs\scheduler.log 2>&1"

REM Attendre 5 secondes
timeout /t 5 /nobreak > nul

REM Demarrer le webserver en arriere-plan
echo [2/2] Demarrage Airflow Webserver (port 8080)...
start "Airflow Webserver" /MIN cmd /c "call .venv\Scripts\activate.bat && airflow webserver >> airflow\logs\webserver.log 2>&1"

echo.
echo ============================================================
echo Airflow DEMARRE en arriere-plan
echo ============================================================
echo.
echo Web UI: http://localhost:8080
echo Logs: %AIRFLOW_HOME%\logs\
echo.
echo Pour verifier l'etat: check_airflow_status.bat
echo Pour arreter: Gestionnaire des taches -^> Terminer processus Python Airflow
echo.
pause
