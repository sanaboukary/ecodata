@echo off
title Mise a Jour Toutes Sources
color 0C

cls
echo ================================================================================
echo           MISE A JOUR COMPLETE - TOUTES LES SOURCES DE DONNEES
echo ================================================================================
echo.
echo  Ce script va collecter les donnees RECENTES manquantes pour:
echo.
echo  🌍 World Bank    - Indicateurs macroeconomiques (8 pays CEDEAO)
echo  💰 IMF           - Donnees monetaires et financieres
echo  🏛️  AfDB          - Banque Africaine de Developpement
echo  🎯 UN SDG        - Objectifs de Developpement Durable
echo.
echo  Note: BRVM collecte deja automatique (toutes les heures)
echo.
echo ================================================================================
echo.

choice /C ON /M "Lancer la mise a jour complete de TOUTES les sources"

if errorlevel 2 goto FIN

cls
echo ================================================================================
echo                          COLLECTE EN COURS
echo ================================================================================
echo.
echo  Ceci peut prendre 10-30 minutes selon la connexion...
echo.

python mettre_a_jour_toutes_sources.py

echo.
echo ================================================================================
echo                          COLLECTE TERMINEE
echo ================================================================================
echo.
echo  Verification des donnees collectees...
echo.

python resumer_toutes_sources.py

echo.
echo ================================================================================
echo  Dashboard: http://127.0.0.1:8000/
echo  Marketplace: http://127.0.0.1:8000/marketplace/
echo ================================================================================
echo.

:FIN
pause
