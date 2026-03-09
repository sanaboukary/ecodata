@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat

echo ========================================
echo ANALYSE DES DONNEES BRVM
echo ========================================
python analyser_structure_brvm.py
echo.
echo ========================================
echo DONNEES COLLECTEES AUJOURD'HUI
echo ========================================
python voir_donnees_aujourdhui.py
pause
