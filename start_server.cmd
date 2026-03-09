@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
echo Demarrage du serveur Django...
python manage.py runserver
