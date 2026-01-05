@echo off
REM COLLECTE BRVM - TOUTES LES SOLUTIONS

echo ================================================================================
echo         COLLECTEUR BRVM - SOLUTIONS MULTIPLES
echo ================================================================================
echo.
echo Choisissez votre methode de collecte:
echo.
echo [1] COPIER-COLLER depuis navigateur (2 min - 100%% SUCCES)
echo [2] Parser bulletin PDF BRVM (si telecharge)
echo [3] Import CSV manuel (si fichier pret)
echo [4] Voir toutes les solutions disponibles
echo.
echo ================================================================================
echo.

set /p choix="Votre choix (1-4): "

if "%choix%"=="1" goto copier_coller
if "%choix%"=="2" goto parser_pdf
if "%choix%"=="3" goto import_csv
if "%choix%"=="4" goto voir_solutions

:copier_coller
echo.
echo ================================================================================
echo  METHODE 1: COPIER-COLLER DEPUIS NAVIGATEUR
echo ================================================================================
echo.
call .venv\Scripts\activate.bat
python guide_collecte_manuelle.py
echo.
echo Apres avoir colle dans Excel et sauvegarde en CSV:
echo.
pause
echo.
echo Lancement import...
python importer_csv_brvm_complet.py
goto fin

:parser_pdf
echo.
echo ================================================================================
echo  METHODE 2: PARSER BULLETIN PDF
echo ================================================================================
echo.
call .venv\Scripts\activate.bat
python parser_bulletin_brvm.py
goto fin

:import_csv
echo.
echo ================================================================================
echo  METHODE 3: IMPORT CSV MANUEL
echo ================================================================================
echo.
call .venv\Scripts\activate.bat
python importer_csv_brvm_complet.py
goto fin

:voir_solutions
echo.
echo ================================================================================
echo  TOUTES LES SOLUTIONS DISPONIBLES
echo ================================================================================
echo.
type SOLUTION_FINALE_BRVM.md
echo.
echo.
pause
goto menu

:fin
echo.
echo ================================================================================
echo Verification des donnees collectees...
echo ================================================================================
echo.
python afficher_donnees_aujourdhui.py
echo.
echo ================================================================================
pause
