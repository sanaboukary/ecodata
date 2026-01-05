@echo off
REM Installation des dépendances pour le collecteur BRVM

echo ============================================================
echo INSTALLATION DEPENDANCES COLLECTEUR BRVM
echo ============================================================
echo.

cd /d "%~dp0"

echo Activation environnement virtuel...
call .venv\Scripts\activate.bat

echo.
echo Installation des packages...
pip install --upgrade pip
pip install -r requirements_collecteur.txt

echo.
echo ============================================================
echo INSTALLATION TERMINEE
echo ============================================================
echo.
echo Vous pouvez maintenant lancer:
echo   python collecteur_brvm_ultra_robuste.py
echo   ou
echo   COLLECTER_BRVM.bat
echo.
pause
