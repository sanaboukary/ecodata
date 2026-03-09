@echo off
title Systeme Collecte Automatique BRVM
color 0B

:MENU
cls
echo ================================================================================
echo                    SYSTEME COLLECTE AUTOMATIQUE BRVM
echo ================================================================================
echo.
echo  Collecte TOUTES LES HEURES (9h-16h) TOUS LES JOURS OUVRABLES
echo  Source: https://www.brvm.org/fr/cours-actions/investisseurs
echo  Politique: TOLERANCE ZERO - Donnees REELLES uniquement
echo.
echo ================================================================================
echo.
echo  [1] Collecter MAINTENANT (test)
echo  [2] ACTIVER collecte automatique (Airflow)
echo  [3] VERIFIER statut collecte
echo  [4] DESACTIVER collecte automatique
echo  [5] Voir les LOGS
echo  [6] Dashboard BRVM
echo  [0] Quitter
echo.
echo ================================================================================
echo.

choice /C 1234560 /M "Votre choix"

if errorlevel 7 goto FIN
if errorlevel 6 goto DASHBOARD
if errorlevel 5 goto LOGS
if errorlevel 4 goto DESACTIVER
if errorlevel 3 goto VERIFIER
if errorlevel 2 goto ACTIVER
if errorlevel 1 goto COLLECTER

:COLLECTER
cls
echo ================================================================================
echo                          COLLECTE IMMEDIATE
echo ================================================================================
echo.
python collecter_brvm_horaire_auto.py
echo.
pause
goto MENU

:ACTIVER
cls
echo ================================================================================
echo                    ACTIVATION COLLECTE AUTOMATIQUE
echo ================================================================================
echo.
echo  Configuration Airflow:
echo  - Frequence : Toutes les heures (9h-16h)
echo  - Jours     : Lundi a vendredi
echo  - Retries   : 3 tentatives si echec
echo  - Delai     : 5 minutes entre tentatives
echo.
echo  DAG: brvm_collecte_horaire
echo.
echo ================================================================================
echo.
choice /C ON /M "Confirmer activation"
if errorlevel 2 goto MENU

echo.
echo  Demarrage Airflow en arriere-plan...
start /B cmd /c "start_airflow_background.bat"
timeout /t 5 >nul

echo.
echo  Airflow demarre!
echo  Interface web: http://localhost:8080 (admin/admin)
echo  DAG a activer: brvm_collecte_horaire
echo.
echo  Instructions:
echo  1. Ouvrir http://localhost:8080
echo  2. Chercher DAG: brvm_collecte_horaire
echo  3. Cliquer sur le toggle pour activer
echo.
choice /C O /M "Appuyer sur O pour ouvrir l'interface Airflow"
start http://localhost:8080
echo.
pause
goto MENU

:VERIFIER
cls
echo ================================================================================
echo                         VERIFICATION COLLECTE
echo ================================================================================
echo.
python verifier_collecte_horaire.py
echo.
pause
goto MENU

:DESACTIVER
cls
echo ================================================================================
echo                    DESACTIVATION COLLECTE AUTOMATIQUE
echo ================================================================================
echo.
choice /C ON /M "Confirmer desactivation Airflow"
if errorlevel 2 goto MENU

echo.
echo  Arret Airflow...
taskkill /F /IM airflow.exe 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *airflow*" 2>nul
echo.
echo  Airflow arrete!
echo.
pause
goto MENU

:LOGS
cls
echo ================================================================================
echo                              LOGS COLLECTE
echo ================================================================================
echo.
if exist collecte_brvm_horaire.log (
    echo  Affichage des 50 dernieres lignes...
    echo.
    type collecte_brvm_horaire.log | more
) else (
    echo  Aucun log trouve.
    echo  Le fichier sera cree lors de la premiere collecte.
)
echo.
pause
goto MENU

:DASHBOARD
cls
echo ================================================================================
echo                          DASHBOARD BRVM
echo ================================================================================
echo.
echo  Ouverture du dashboard dans le navigateur...
echo.
start http://127.0.0.1:8000/brvm/
timeout /t 2 >nul
goto MENU

:FIN
echo.
echo  Au revoir!
echo.
exit
