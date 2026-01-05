@echo off
REM Script pour planifier la collecte BRVM quotidienne avec Windows Task Scheduler
REM Crée une tâche qui s'exécute à 17h00 du lundi au vendredi

echo ============================================================
echo PLANIFICATION COLLECTE BRVM - Windows Task Scheduler
echo ============================================================
echo.

set SCRIPT_DIR=%~dp0
set SCRIPT_PATH=%SCRIPT_DIR%collecte_brvm_simple.py
set PYTHON_PATH=%SCRIPT_DIR%.venv\Scripts\python.exe
set TASK_NAME=CollecteBRVM_Quotidienne

echo Dossier du projet: %SCRIPT_DIR%
echo Script Python: %SCRIPT_PATH%
echo Interpreteur Python: %PYTHON_PATH%
echo.

REM Supprimer la tâche existante si elle existe
echo Suppression de la tâche existante (si elle existe)...
schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1

REM Créer la nouvelle tâche planifiée
echo Creation de la tâche planifiée...
echo   - Nom: %TASK_NAME%
echo   - Heure: 17:00 (lundi-vendredi)
echo   - Action: Collecte BRVM automatique
echo.

schtasks /Create ^
  /TN "%TASK_NAME%" ^
  /TR "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\"" ^
  /SC WEEKLY ^
  /D MON,TUE,WED,THU,FRI ^
  /ST 17:00 ^
  /RU "%USERNAME%" ^
  /RL HIGHEST ^
  /F

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo ✅ TACHE PLANIFIEE CREEE AVEC SUCCES
    echo ============================================================
    echo.
    echo La collecte BRVM s'executera automatiquement:
    echo   - Tous les jours ouvrables (lundi-vendredi)
    echo   - A 17h00 (apres cloture BRVM a 16h30)
    echo.
    echo Pour gerer la tâche:
    echo   - Ouvrir: Gestionnaire des tâches
    echo   - Chercher: %TASK_NAME%
    echo.
    echo Pour tester immédiatement:
    echo   schtasks /Run /TN "%TASK_NAME%"
    echo.
    echo Pour voir les details:
    echo   schtasks /Query /TN "%TASK_NAME%" /V /FO LIST
    echo.
) else (
    echo.
    echo ============================================================
    echo ❌ ERREUR LORS DE LA CREATION DE LA TACHE
    echo ============================================================
    echo.
    echo Assurez-vous d'executer ce script en tant qu'administrateur
    echo.
)

pause
