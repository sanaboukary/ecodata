@echo off
echo Activation de l'environnement virtuel...
call .venv\Scripts\activate.bat

echo.
echo Lancement du serveur Django...
echo Serveur disponible sur : http://localhost:8000
echo.
echo Appuyez sur Ctrl+C pour arreter le serveur
echo.

python manage.py runserver
