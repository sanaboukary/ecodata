@echo off
chcp 65001 > nul
echo.
echo ====================================================================
echo 🔄 COLLECTEUR BRVM AUTOMATIQUE - BOUCLE HORAIRE
echo ====================================================================
echo.
echo ✅ Collecte automatique 9h-16h (lun-ven)
echo ✅ Protection anti-bannissement
echo ✅ Tous attributs : Prix + Volume + Variation + Volatilité + OHLC
echo.
echo 📝 Logs : collecte_brvm_horaire.log
echo ⏸️  Arrêt : Ctrl+C
echo.
echo ====================================================================
echo.

cd /d "%~dp0"

REM Activer environnement virtuel
call .venv\Scripts\activate.bat

REM Lancer collecteur
echo 🚀 Démarrage du collecteur...
echo.
python collecter_brvm_boucle_horaire.py

pause
