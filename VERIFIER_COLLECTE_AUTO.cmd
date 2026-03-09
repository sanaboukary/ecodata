@echo off
chcp 65001 >nul
cd /d "%~dp0"
call .venv\Scripts\activate.bat

cls
python verifier_collecte_auto.py

echo.
echo ╔═══════════════════════════════════════════════════════════════════════════╗
echo ║  PRESS ANY KEY TO CLOSE                                                   ║
echo ╚═══════════════════════════════════════════════════════════════════════════╝
pause >nul
