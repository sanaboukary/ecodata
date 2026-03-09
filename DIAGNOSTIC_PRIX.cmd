@echo off
chcp 65001 >nul
cd /d "%~dp0"
call .venv\Scripts\activate.bat

echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║  DIAGNOSTIC ET CORRECTION DES PRIX BRVM                                   ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.

python diagnostic_prix_brvm.py

echo.
echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║  Appuyez sur une touche pour continuer...                                 ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
pause >nul
