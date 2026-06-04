@echo off
title Adamsy Free TV
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
)

".venv\Scripts\python.exe" -m pip install -r requirements.txt -q
echo Starting API + web UI at http://127.0.0.1:8001/
start "Adamsy Free TV API" cmd /k "cd /d "%~dp0" && .venv\Scripts\python.exe tv_main.py --serve-api --host 127.0.0.1 --port 8001"
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8001/"
echo Adamsy Free TV is running.
pause
