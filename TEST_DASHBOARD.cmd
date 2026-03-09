@echo off
chcp 65001 >nul
cd /d "%~dp0"
call .venv\Scripts\activate.bat

echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║  TEST DES DONNÉES BRVM - DASHBOARD                                        ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
echo.

python test_dashboard_data.py

echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║  PRESS ANY KEY TO CLOSE                                                   ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
pause >nul
