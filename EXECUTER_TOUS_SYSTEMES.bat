@echo off
echo ================================================================================
echo EXECUTION COMPLETE - TOUS LES SYSTEMES DE RECOMMANDATIONS
echo ================================================================================
echo.

REM Activation environnement
call .venv\Scripts\activate.bat

echo [1/2] Execution TOP5 ENGINE (Classement Surperformance)...
echo ────────────────────────────────────────────────────────────────────────────
python top5_engine_brvm.py
if %errorlevel% neq 0 (
    echo ERREUR: TOP5 ENGINE echoue
    pause
    exit /b 1
)

echo.
echo [2/2] Execution DECISION FINALE (MODE INSTITUTIONAL + ELITE)...
echo ────────────────────────────────────────────────────────────────────────────
python decision_finale_brvm.py
if %errorlevel% neq 0 (
    echo ERREUR: Decision finale echouee
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo ✅ EXECUTION COMPLETE - LES DEUX SYSTEMES SONT GENERES
echo ================================================================================
echo.
echo Pour afficher les resultats:
echo   1. TOP5 ENGINE:              python afficher_top5_engine.py
echo   2. MODE INSTITUTIONAL+ELITE: python afficher_decision_finale.py
echo   3. COMPARAISON:              python comparer_systemes.py
echo.

pause
