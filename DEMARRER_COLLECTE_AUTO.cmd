@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║  🚀 DÉMARRAGE COLLECTE AUTOMATIQUE HORAIRE BRVM                           ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.
echo Vous avez 2 options pour la collecte automatique:
echo.
echo   1️⃣  AIRFLOW (Recommandé pour production)
echo      ✅ Interface Web complète
echo      ✅ Gestion avancée des DAGs
echo      ✅ Historique et monitoring
echo      ⚠️  Plus complexe à configurer
echo.
echo   2️⃣  APScheduler (Simple et rapide)
echo      ✅ Installation simple
echo      ✅ Configuration légère
echo      ✅ Logs en temps réel
echo      ⚠️  Pas d'interface graphique
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo.
set /p choix="Choisissez une option (1 ou 2): "

if "%choix%"=="1" goto AIRFLOW
if "%choix%"=="2" goto APSCHEDULER

echo ❌ Choix invalide
pause
exit /b

:AIRFLOW
cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║  🌊 DÉMARRAGE AIRFLOW                                                     ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.
echo 📋 Étapes:
echo    1. Démarrage du scheduler et webserver Airflow...
echo    2. Ouvrez http://localhost:8080 dans votre navigateur
echo    3. Connectez-vous (admin/admin)
echo    4. Activez le DAG 'brvm_collecte_horaire'
echo.
echo ⏳ Démarrage en cours...
echo.

call start_airflow_background.bat

echo.
echo ✅ Airflow démarré!
echo.
echo 💡 Prochaines étapes:
echo    1. Ouvrez: http://localhost:8080
echo    2. User: admin
echo    3. Pass: admin
echo    4. Activez le toggle du DAG 'brvm_collecte_horaire'
echo.
pause
exit /b

:APSCHEDULER
cls
echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║  ⏰ DÉMARRAGE APSCHEDULER - COLLECTE HORAIRE BRVM                         ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.
echo 📋 Configuration:
echo    • Collecte toutes les heures de 9h à 15h (heures de marché)
echo    • Vérification quotidienne à 17h
echo    • Logs dans: logs/brvm_collecte_horaire.log
echo.
echo ⏳ Démarrage du scheduler...
echo.

call .venv\Scripts\activate.bat

python scheduler_horaire_brvm.py

echo.
echo ✅ Scheduler arrêté
pause
exit /b
