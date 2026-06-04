$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
  throw "Virtual environment not found. Build or install dependencies first."
}

& $python tv_main.py --serve-api --host 127.0.0.1 --port 8000
