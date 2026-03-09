@echo off
REM Moniteur de collecte World Bank en temps reel

cd /d "E:\DISQUE C\Desktop\Implementation plateforme"

echo.
echo ===============================================
echo  MONITEUR COLLECTE WORLD BANK
echo ===============================================
echo.

call .venv\Scripts\activate.bat

:LOOP
cls
python moniteur_collecte.py
timeout /t 30 /nobreak
goto LOOP
