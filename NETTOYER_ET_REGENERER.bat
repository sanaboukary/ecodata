@echo off
echo ========================================
echo    NETTOYAGE OUTLIERS BRVM - TRADING
echo ========================================
echo.
echo Objectif: Nettoyer les 80 outliers detectes
echo Strategy: Conserver opportunites, supprimer erreurs
echo.

call .venv\Scripts\activate.bat

echo [ETAPE 1/4] Nettoyage outliers...
python nettoyer_outliers_trading.py
if errorlevel 1 (
    echo [ERREUR] Echec nettoyage
    pause
    exit /b 1
)

echo.
echo [ETAPE 2/4] Validation qualite...
python valider_qualite_brvm.py
if errorlevel 1 (
    echo [ERREUR] Echec validation
    pause
    exit /b 1
)

echo.
echo [ETAPE 3/4] Regeneration analyses IA...
python analyse_ia_simple.py
if errorlevel 1 (
    echo [ERREUR] Echec analyses
    pause
    exit /b 1
)

echo.
echo [ETAPE 4/4] Regeneration TOP5 hebdomadaire...
python workflow_production_django.py
if errorlevel 1 (
    echo [ERREUR] Echec workflow
    pause
    exit /b 1
)

echo.
echo ========================================
echo    NETTOYAGE TERMINE AVEC SUCCES
echo ========================================
echo.
echo Outliers nettoyes selon objectif TRADING
echo Recommandations TOP5 mises a jour avec donnees propres
echo.
echo Dashboard disponible: http://127.0.0.1:8000/brvm/recommendations/
echo.
pause
