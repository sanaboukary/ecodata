@echo off
echo.
echo ================================================================================
echo  PIPELINE BRVM EXPERT - MOTEUR TOP 5 HEBDOMADAIRE
echo ================================================================================
echo.
echo [PHASE 2] WOS_TOP5 : Momentum court terme (sentiment 20%%)
echo [PHASE 3] Freins ajustes : Penalisation RSI (pas blocage)
echo [PHASE 4] Smart Money : Liquidite institutionnelle
echo [PHASE 6] Relative Strength : Alpha vs BRVM Composite
echo [PHASE 5] Contrainte sectorielle : Max 3 actions/secteur
echo [PHASE 7] Probabilite Top 5 : Sigmoid calibre
echo [PHASE 9] Capture Rate : Mesure d'edge historique
echo [PHASE 10] Nettoyage : ATR%% plafonne a 30%%
echo.
echo ================================================================================
echo.

echo [ETAPE 1/5] Analyse technique...
.\.venv\Scripts\python.exe analyse_ia_simple.py
if errorlevel 1 (
    echo ERREUR: Analyse technique echouee
    pause
    exit /b 1
)

echo.
echo [ETAPE 2/5] Decision finale (WOS_TOP5)...
.\.venv\Scripts\python.exe decision_finale_brvm.py
if errorlevel 1 (
    echo ERREUR: Decision finale echouee
    pause
    exit /b 1
)

echo.
echo [ETAPE 3/5] Generation Top 5 Expert...
.\.venv\Scripts\python.exe top5_engine_brvm.py
if errorlevel 1 (
    echo ERREUR: Top5 engine echoue
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo  PIPELINE TERMINE AVEC SUCCES
echo ================================================================================
echo.
echo Consultez le Top 5 dans MongoDB : collection top5_weekly_brvm
echo Dashboard : http://127.0.0.1:8000/brvm/recommendations/
echo.
pause
