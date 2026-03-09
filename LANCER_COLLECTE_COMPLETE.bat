@echo off
chcp 65001 >nul
echo ================================================================================
echo   COLLECTE COMPLETE - TOUTES SOURCES INTERNATIONALES (1990-2026)
echo ================================================================================
echo.
echo  Sources:
echo    - World Bank (11 indicateurs x 8 pays = 88 combinaisons)
echo    - IMF (8 series x 8 pays = 64 combinaisons)
echo    - AfDB (6 indicateurs x 8 pays = 48 combinaisons)
echo    - UN SDG (6 series x 8 pays = 48 combinaisons)
echo.
echo  Periode: 1990-2026 (37 ans)
echo  Duree estimee: 10-15 minutes
echo.
echo ================================================================================
echo.

cd /d "E:\DISQUE C\Desktop\Implementation plateforme"

echo [1/4] Lancement collecte WORLD BANK...
start /B cmd /c "python collecter_worldbank_complet.py > collecte_wb_log.txt 2>&1"
timeout /t 2 /nobreak >nul

echo [2/4] Lancement collecte IMF...
start /B cmd /c "python collecter_imf_complet.py > collecte_imf_log.txt 2>&1"
timeout /t 2 /nobreak >nul

echo [3/4] Lancement collecte AfDB + UN SDG...
start /B cmd /c "python collecter_afdb_un_complet.py > collecte_afdb_un_log.txt 2>&1"
timeout /t 2 /nobreak >nul

echo.
echo ================================================================================
echo   COLLECTES LANCEES EN ARRIERE-PLAN
echo ================================================================================
echo.
echo  Fichiers log:
echo    - collecte_wb_log.txt (World Bank)
echo    - collecte_imf_log.txt (IMF)
echo    - collecte_afdb_un_log.txt (AfDB + UN SDG)
echo.
echo  Pour suivre la progression:
echo    tail -f collecte_wb_log.txt
echo    tail -f collecte_imf_log.txt
echo    tail -f collecte_afdb_un_log.txt
echo.
echo  Pour voir le resume:
echo    python resume_simple.py
echo.
echo ================================================================================

pause
