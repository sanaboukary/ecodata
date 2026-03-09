@echo off
echo ========================================
echo    REDEMARRAGE SERVEUR DJANGO
echo ========================================
echo.
echo 1. Arret du serveur en cours...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *runserver*" 2>nul
timeout /t 2 /nobreak >nul

echo 2. Activation environnement virtuel...
call .venv\Scripts\activate.bat

echo 3. Lancement serveur Django...
echo.
echo Dashboard disponible a : http://127.0.0.1:8000/brvm/recommendations/
echo.
python manage.py runserver 127.0.0.1:8000
