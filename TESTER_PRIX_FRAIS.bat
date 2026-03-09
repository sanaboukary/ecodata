@echo off
echo ========================================
echo TEST DES PRIX FRAIS - PIPELINE COMPLET
echo ========================================
echo.

REM 1. Relancer le pipeline complet
echo [ETAPE 1/3] Execution pipeline BRVM (decisions + top5)...
.\.venv\Scripts\python.exe pipeline_brvm.py
if errorlevel 1 (
    echo ERREUR: Pipeline echoue
    pause
    exit /b 1
)

echo.
echo [ETAPE 2/3] Verification des prix dans MongoDB...
.\.venv\Scripts\python.exe -c "from plateforme_centralisation.mongo import get_mongo_db; from datetime import datetime; _, db = get_mongo_db(); top5 = list(db.top5_weekly_brvm.find().sort('rank',1)); print('\n=== TOP 5 AVEC PRIX FRAIS ==='); [print(f'{i}. {r[\"symbol\"]:6s} | Prix: {r.get(\"prix_entree\",0):>8.0f} FCFA | Gain: {r.get(\"gain_attendu\",0):>5.1f}%% | Cible: {r.get(\"prix_cible\",0):>8.0f} FCFA') for i,r in enumerate(top5,1)]"

echo.
echo [ETAPE 3/3] Ouvrir le dashboard...
echo.
echo Dashboard disponible: http://127.0.0.1:8000/brvm/recommendations/
echo.
echo Verifiez que les prix affiches correspondent aux derniers prix collectes.
echo.
pause
