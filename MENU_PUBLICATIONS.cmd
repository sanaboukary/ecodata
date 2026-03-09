@echo off
title Systeme Publications BRVM - Menu Principal
color 0B

:MENU
cls
echo ================================================================================
echo           SYSTEME INTELLIGENT PUBLICATIONS BRVM
echo ================================================================================
echo.
echo  Collecte automatique + Analyse sentiment pour trading decisions
echo.
echo  [1] COLLECTER publications BRVM (toutes categories)
echo.
echo  [2] ANALYSER sentiment (generer signaux BUY/HOLD/SELL)
echo.
echo  [3] TESTER systeme (verification complete)
echo.
echo  [4] VOIR dashboard web
echo.
echo  [5] LIRE documentation complete
echo.
echo  [6] ACTIVER Airflow (collecte quotidienne automatique)
echo.
echo  [Q] QUITTER
echo.
echo ================================================================================
echo.

choice /C 123456Q /N /M "Votre choix : "

if errorlevel 7 goto END
if errorlevel 6 goto AIRFLOW
if errorlevel 5 goto DOCS
if errorlevel 4 goto DASHBOARD
if errorlevel 3 goto TEST
if errorlevel 2 goto ANALYZE
if errorlevel 1 goto COLLECT

:COLLECT
cls
echo.
echo  Lancement collecte publications...
echo.
COLLECTER_PUBLICATIONS_BRVM.cmd
pause
goto MENU

:ANALYZE
cls
echo.
echo  Lancement analyse sentiment...
echo.
ANALYSER_SENTIMENT.cmd
pause
goto MENU

:TEST
cls
echo.
echo  Test systeme complet...
echo.
python test_publications_system.py
echo.
pause
goto MENU

:DASHBOARD
echo.
echo  Ouverture dashboard dans navigateur...
start http://127.0.0.1:8000/brvm/publications/
timeout /t 2 >nul
goto MENU

:DOCS
cls
type SYSTEME_PUBLICATIONS_README.txt
echo.
pause
goto MENU

:AIRFLOW
cls
echo.
echo  Activation Airflow...
echo.
start_airflow_background.bat
echo.
echo  Airflow Web UI : http://localhost:8080/
echo  Activer DAG : brvm_publications_quotidien
echo.
pause
goto MENU

:END
exit
