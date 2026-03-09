@echo off
title Collecte Publications BRVM
color 0A

echo ===============================================================================
echo           COLLECTEUR INTELLIGENT PUBLICATIONS BRVM
echo ===============================================================================
echo.
echo  Collecte automatique de TOUTES les publications officielles :
echo  - Bulletins Officiels de la Cote (quotidiens)
echo  - Communiques financiers (resultats, dividendes)
echo  - Rapports annuels des societes cotees
echo  - Convocations AG
echo  - Avis de suspension/cotation
echo  - Actualites BRVM
echo.
echo ===============================================================================
echo.

choice /C 123 /M "Choisissez : [1] Collecte COMPLETE  [2] Test rapide (30 par categorie)  [3] Une categorie"

if errorlevel 3 goto ONE_CATEGORY
if errorlevel 2 goto TEST
if errorlevel 1 goto FULL

:FULL
echo.
echo  Lancement collecte COMPLETE (peut prendre 5-10 minutes)...
echo.
python collecter_publications_brvm_intelligent.py
goto END

:TEST
echo.
echo  Lancement collecte TEST (30 publications par categorie)...
echo.
python collecter_publications_brvm_intelligent.py --limit 30
goto END

:ONE_CATEGORY
echo.
echo  Categories disponibles :
echo  - BULLETIN_OFFICIEL
echo  - COMMUNIQUE_RESULTATS
echo  - COMMUNIQUE_DIVIDENDE
echo  - COMMUNIQUE_AG
echo  - RAPPORT_SOCIETE
echo  - ACTUALITE
echo  - COMMUNIQUE_SUSPENSION
echo.
set /p CATEGORY="Entrez le nom de la categorie : "
echo.
python collecter_publications_brvm_intelligent.py --category %CATEGORY%
goto END

:END
echo.
echo ===============================================================================
echo  Verification : http://127.0.0.1:8000/brvm/publications/
echo ===============================================================================
echo.
pause
