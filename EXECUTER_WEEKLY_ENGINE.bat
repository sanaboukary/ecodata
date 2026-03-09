@echo off
chcp 65001 >nul
echo ================================================================================
echo WEEKLY ENGINE EXPERT - RECOMMANDATIONS HYBRIDES BRVM
echo ================================================================================
echo.

cd /d "e:\DISQUE C\Desktop\Implementation plateforme"

echo [ÉTAPE 1/3] Calcul RSI manuel (workaround bug pipeline)...
.venv\Scripts\python.exe calc_rsi_simple.py
if errorlevel 1 (
    echo ❌ Erreur calcul RSI
    pause
    exit /b 1
)
echo ✅ RSI calculé
echo.

echo [ÉTAPE 2/3] Vérification données weekly W06...
.venv\Scripts\python -c "from pymongo import MongoClient; db=MongoClient()['centralisation_db']; w=db.prices_weekly.count_documents({'week':'2026-W06'}); print(f'Actions W06: {w}'); exit(0 if w>0 else 1)"
if errorlevel 1 (
    echo ⚠️ Pas de données W06, rebuild nécessaire
    echo.
    echo Rebuild automatique...
    .venv\Scripts\python.exe rebuild_weekly_direct.py
)
echo.

echo [ÉTAPE 3/3] Génération recommandations HYBRIDES (Technique + Fondamental)...
echo.
.venv\Scripts\python.exe brvm_pipeline\weekly_engine_expert.py --week 2026-W06

echo.
echo ================================================================================
echo Recommandations sauvegardées dans MongoDB : decisions_brvm_weekly
echo Mode : EXPERT_BRVM (Hybride)
echo ================================================================================
echo.

pause
