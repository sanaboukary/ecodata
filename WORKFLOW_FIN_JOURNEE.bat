@echo off
REM ========================================================================
REM WORKFLOW FIN DE JOURNEE - TOLÉRANCE ZÉRO
REM ========================================================================
REM
REM Exécution : Chaque soir après dernière collecte (16h30)
REM
REM Ce script :
REM 1. Agrège les collectes intraday 9h-16h → VRAIS high/low
REM 2. Met à jour prices_daily
REM 3. En fin de semaine (vendredi) : rebuild weekly + recommandations
REM
REM ========================================================================

cd /d "e:\DISQUE C\Desktop\Implementation plateforme"

echo.
echo ========================================================================
echo WORKFLOW FIN DE JOURNEE - %date% %time:~0,5%
echo ========================================================================
echo.

REM ========================================
REM ÉTAPE 1: Build Daily (agrège 9h-16h)
REM ========================================
echo [1/3] Agrégation collectes intraday 9h-16h...
.venv\Scripts\python.exe build_daily.py
if errorlevel 1 (
    echo.
    echo ERREUR lors de build_daily.py
    pause
    exit /b 1
)

REM ========================================
REM ÉTAPE 2: Si vendredi → Rebuild Weekly
REM ========================================
for /f "skip=1" %%d in ('wmic path Win32_LocalTime get DayOfWeek') do (
    set dow=%%d
    goto :got_dow
)
:got_dow

echo.
if "%dow%"=="5" (
    echo [2/3] VENDREDI - Rebuild weekly + indicateurs...
    .venv\Scripts\python.exe rebuild_weekly_direct.py
    if errorlevel 1 (
        echo.
        echo ERREUR lors de rebuild_weekly
        pause
        exit /b 1
    )
    
    echo.
    echo [3/3] Calcul RSI + Génération recommandations...
    .venv\Scripts\python.exe calc_rsi_simple.py
    .venv\Scripts\python.exe reco_final.py
    
    echo.
    echo ========================================================================
    echo ✅ WORKFLOW COMPLET - RECOMMANDATIONS GÉNÉRÉES
    echo ========================================================================
    echo.
    echo Consulter recommandations ci-dessus
    echo.
) else (
    echo [2/3] Jour ouvré - Skip rebuild weekly (vendredi uniquement)
    echo [3/3] Skip recommandations
    echo.
    echo ========================================================================
    echo ✅ DAILY QUOTIDIEN - VRAIS HIGH/LOW CALCULÉS
    echo ========================================================================
    echo.
)

pause
