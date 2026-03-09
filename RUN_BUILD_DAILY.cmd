@echo off
setlocal

REM Run from project root
cd /d "%~dp0"

REM Use venv python if present
if exist ".venv\Scripts\python.exe" (
  set "PY=.venv\Scripts\python.exe"
) else (
  set "PY=python"
)

REM By default, build for today. You can pass: --yesterday or --date YYYY-MM-DD
%PY% build_daily.py %*

endlocal
