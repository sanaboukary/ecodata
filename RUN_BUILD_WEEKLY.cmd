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

%PY% build_weekly.py %*

endlocal
