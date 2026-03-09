@echo off
chcp 65001 >nul
cd /d "E:\DISQUE C\Desktop\Implementation plateforme"
"E:\DISQUE C\Desktop\Implementation plateforme\.venv\Scripts\python.exe" inventaire_brvm_final.py
echo.
echo ===================================================
echo Rapport genere : INVENTAIRE_BRVM_RESULTAT.txt
echo ===================================================
pause
