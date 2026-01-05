@echo off
REM Verification de l'etat d'Airflow

echo ============================================================
echo VERIFICATION ETAT AIRFLOW
echo ============================================================
echo.

echo Recherche processus Airflow...
tasklist /FI "IMAGENAME eq python.exe" /FO TABLE | findstr /I "python.exe"

echo.
echo ------------------------------------------------------------
echo Logs recents:
echo ------------------------------------------------------------

if exist airflow\logs\scheduler\latest (
    echo.
    echo [Scheduler - 10 dernieres lignes]
    powershell -Command "Get-Content airflow\logs\scheduler.log -Tail 10 -ErrorAction SilentlyContinue"
)

if exist airflow\logs\webserver.log (
    echo.
    echo [Webserver - 10 dernieres lignes]
    powershell -Command "Get-Content airflow\logs\webserver.log -Tail 10 -ErrorAction SilentlyContinue"
)

echo.
echo ============================================================
echo Web UI: http://localhost:8080
echo ============================================================
echo.
pause
