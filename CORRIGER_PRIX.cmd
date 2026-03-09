@echo off
chcp 65001 >nul
cd /d "%~dp0"
call .venv\Scripts\activate.bat

echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║  🔧 CORRECTION FORCÉE DES PRIX BRVM                                       ║
echo ║                                                                            ║
echo ║  Ce script va:                                                             ║
echo ║  1. Supprimer toutes les anciennes données avec faux prix                 ║
echo ║  2. Insérer les VRAIS prix d'aujourd'hui                                  ║
echo ║  3. Vérifier que les données sont correctes                               ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.
echo ⚠️  Appuyez sur une touche pour continuer ou fermez cette fenêtre pour annuler
pause >nul

cls
echo.
echo 🚀 Correction en cours...
echo.

python CORRIGER_PRIX_FORCE.py

echo.
echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║  ✅ TERMINÉ!                                                               ║
echo ║                                                                            ║
echo ║  Rafraîchissez votre navigateur (Ctrl+F5) pour voir les nouveaux prix    ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.
pause
