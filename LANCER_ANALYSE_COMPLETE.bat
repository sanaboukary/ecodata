@echo off
cd /d "e:\DISQUE C\Desktop\Implementation plateforme"

echo ========================================
echo ANALYSE SEMANTIQUE + AGREGATION + PIPELINE
echo ========================================

echo.
echo [1/3] Analyse semantique V3...
.venv\Scripts\python.exe analyse_semantique_brvm_v3.py
echo DONE

echo.
echo [2/3] Agregation par action...
.venv\Scripts\python.exe agregateur_semantique_actions.py
echo DONE

echo.
echo [3/3] Verification resultats...
.venv\Scripts\python.exe diagnostic_semantic_rapide.py

echo.
echo ========================================
echo TERMINE!
echo ========================================
pause
