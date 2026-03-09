@echo off
chcp 65001 >nul
echo ================================================================================
echo   COLLECTE TOUTES LES SOURCES INTERNATIONALES
echo ================================================================================
echo.

cd /d "E:\DISQUE C\Desktop\Implementation plateforme"

echo [1/4] World Bank - Population Cote d'Ivoire...
python manage.py ingest_source --source worldbank --indicator SP.POP.TOTL --country CI
echo.

echo [2/4] World Bank - PIB Senegal...
python manage.py ingest_source --source worldbank --indicator NY.GDP.MKTP.CD --country SN
echo.

echo [3/4] IMF - CPI Cote d'Ivoire...
python manage.py ingest_source --source imf --series PCPI_IX --area CI
echo.

echo [4/4] IMF - CPI Senegal...
python manage.py ingest_source --source imf --series PCPI_IX --area SN
echo.

echo ================================================================================
echo   COLLECTE TERMINEE
echo ================================================================================
pause
