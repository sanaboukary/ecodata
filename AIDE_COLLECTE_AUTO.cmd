@echo off
chcp 65001 >nul
cls

echo.
echo ╔═══════════════════════════════════════════════════════════════════════════════╗
echo ║                                                                                ║
echo ║  ✅ VOTRE SYSTÈME DE COLLECTE AUTOMATIQUE EST PRÊT!                           ║
echo ║                                                                                ║
echo ╚═══════════════════════════════════════════════════════════════════════════════╝
echo.
echo.
echo 🎯 POUR DÉMARRER LA COLLECTE HORAIRE AUTOMATIQUE:
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
echo   📂 Double-cliquez sur: DEMARRER_COLLECTE_AUTO.cmd
echo.
echo   Puis choisissez:
echo     1️⃣  Airflow (Interface Web - Recommandé pour production)
echo     2️⃣  APScheduler (Simple - Recommandé pour démarrer)
echo.
echo.
echo 🔍 VÉRIFIER QUE ÇA FONCTIONNE:
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
echo   📂 Double-cliquez sur: TEST_DASHBOARD.cmd
echo.
echo   Ou exécutez: python verifier_collecte_auto.py
echo.
echo.
echo 🛠️  CORRECTION DES PRIX (SI NÉCESSAIRE):
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
echo   📂 Double-cliquez sur: CORRIGER_PRIX.cmd
echo.
echo   Cela va:
echo     ✅ Supprimer les anciens prix simulés
echo     ✅ Insérer les vrais prix d'aujourd'hui
echo     ✅ Vérifier que tout est correct
echo.
echo.
echo ⏰ PLANIFICATION AUTOMATIQUE:
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
echo   • Collecte BRVM: Toutes les heures de 9h à 15h (lundi-vendredi)
echo   • Vérification qualité: Tous les jours à 17h
echo   • Méthode: Scraping site officiel BRVM
echo   • Politique: Données réelles UNIQUEMENT (zéro simulation)
echo.
echo.
echo 📊 DASHBOARD:
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
echo   1. Démarrez le serveur: start_server.cmd
echo   2. Ouvrez: http://127.0.0.1:8000/
echo   3. Recommandations: http://127.0.0.1:8000/brvm/recommendations/
echo.
echo.
echo 📖 DOCUMENTATION COMPLÈTE:
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
echo   Consultez: GUIDE_COLLECTE_AUTO.md
echo.
echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo.
pause
