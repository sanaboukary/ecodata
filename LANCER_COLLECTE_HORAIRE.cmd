@echo off
title Collecte BRVM Horaire Automatique
color 0A

echo ===============================================================================
echo           COLLECTE BRVM HORAIRE AUTOMATIQUE
echo ===============================================================================
echo.
echo  Collecte les cours BRVM toutes les heures (9h-16h) tous les jours ouvrables
echo  Source: https://www.brvm.org/fr/cours-actions/investisseurs
echo  Politique: TOLERANCE ZERO - Donnees reelles uniquement
echo.
echo ===============================================================================
echo.

choice /C 123 /M "Choisir: [1] Collecter MAINTENANT  [2] Activer Airflow (auto)  [3] Test connexion BRVM"

if errorlevel 3 goto TEST
if errorlevel 2 goto AIRFLOW
if errorlevel 1 goto NOW

:NOW
echo.
echo  Lancement collecte immediate...
echo.
python collecter_brvm_horaire_auto.py
goto END

:AIRFLOW
echo.
echo  Activation collecte automatique Airflow...
echo.
echo  Configuration:
echo  - Frequence: Toutes les heures (9h-16h)
echo  - Jours: Lundi a vendredi
echo  - Retries: 3 tentatives si echec
echo.
start_airflow_background.bat
echo.
echo  Airflow demarre! Verifier sur http://localhost:8080
echo  DAG: brvm_collecte_horaire
echo.
goto END

:TEST
echo.
echo  Test de connexion au site BRVM...
echo.
python -c "import requests; r=requests.get('https://www.brvm.org/fr/cours-actions/investisseurs', verify=False, timeout=10); print(f'Status: {r.status_code}'); print(f'Taille: {len(r.content)} bytes'); print('OK!' if r.status_code==200 else 'ERREUR!')"
goto END

:END
echo.
echo ===============================================================================
echo  Dashboard: http://127.0.0.1:8000/brvm/
echo  Logs: collecte_brvm_horaire.log
echo ===============================================================================
echo.
pause
