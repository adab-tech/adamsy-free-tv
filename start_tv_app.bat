@echo off
setlocal
cd /d "%~dp0"
set "LOG_FILE=%~dp0tv_start.log"

echo [%date% %time%] Launch request >> "%LOG_FILE%"

if exist "dist\VirtualTV.exe" (
  echo [%date% %time%] Launching dist\VirtualTV.exe >> "%LOG_FILE%"
  start "" "%~dp0dist\VirtualTV.exe"
  exit /b 0
)

if exist ".venv\Scripts\pythonw.exe" (
  echo [%date% %time%] Launching .venv\Scripts\pythonw.exe via runpy tv_main.py >> "%LOG_FILE%"
  start "" "%~dp0.venv\Scripts\pythonw.exe" -c "import runpy; runpy.run_path(r'%~dp0tv_main.py', run_name='__main__')"
  exit /b 0
)

if exist ".venv\Scripts\python.exe" (
  echo [%date% %time%] Launching .venv\Scripts\python.exe via runpy tv_main.py >> "%LOG_FILE%"
  start "" "%~dp0.venv\Scripts\python.exe" -c "import runpy; runpy.run_path(r'%~dp0tv_main.py', run_name='__main__')"
  exit /b 0
)

if exist "%LocalAppData%\Programs\Python\Python314\pythonw.exe" (
  echo [%date% %time%] Launching Python314\pythonw.exe via runpy tv_main.py >> "%LOG_FILE%"
  start "" "%LocalAppData%\Programs\Python\Python314\pythonw.exe" -c "import runpy; runpy.run_path(r'%~dp0tv_main.py', run_name='__main__')"
  exit /b 0
)

if exist "%LocalAppData%\Programs\Python\Python314\python.exe" (
  echo [%date% %time%] Launching Python314\python.exe via runpy tv_main.py >> "%LOG_FILE%"
  start "" "%LocalAppData%\Programs\Python\Python314\python.exe" -c "import runpy; runpy.run_path(r'%~dp0tv_main.py', run_name='__main__')"
  exit /b 0
)

echo [%date% %time%] Launching PATH python tv_main.py >> "%LOG_FILE%"
start "" python "%~dp0tv_main.py"
