@echo off
title Collecte BRVM Manuelle
color 0E

echo ===============================================================================
echo                    COLLECTE BRVM - SAISIE MANUELLE
echo ===============================================================================
echo.
echo  POLITIQUE TOLERANCE ZERO: Donnees REELLES uniquement
echo.
echo  INSTRUCTIONS:
echo.
echo  1. Ouvrir: https://www.brvm.org/fr/cours-actions/investisseurs
echo  2. Noter les cours affiches
echo  3. Modifier VRAIS_COURS_BRVM dans collecter_brvm_manuel.py
echo  4. Relancer ce script
echo.
echo ===============================================================================
echo.

python collecter_brvm_manuel.py

echo.
echo ===============================================================================
echo  Verification : http://127.0.0.1:8000/brvm/
echo ===============================================================================
echo.
pause
