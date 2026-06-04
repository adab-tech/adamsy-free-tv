$ErrorActionPreference = "Stop"

function Resolve-BootstrapPython {
  param(
    [string]$RootPath
  )

  $venvPython = Join-Path $RootPath ".venv\Scripts\python.exe"
  if (Test-Path $venvPython) {
    return $venvPython
  }

  $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
  if ($pyLauncher) {
    return $pyLauncher.Source
  }

  $installedPython = Get-ChildItem "$env:LOCALAPPDATA\Programs\Python" -Directory -ErrorAction SilentlyContinue |
    Sort-Object Name -Descending |
    ForEach-Object { Join-Path $_.FullName "python.exe" } |
    Where-Object { Test-Path $_ } |
    Select-Object -First 1
  if ($installedPython) {
    return $installedPython
  }

  $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
  if ($pythonCmd) {
    return $pythonCmd.Source
  }

  throw "Could not find a usable Python installation."
}

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

& (Join-Path $PSScriptRoot "generate_branding_assets.ps1")
Get-Process -Name "VirtualTV" -ErrorAction SilentlyContinue | Stop-Process -Force

$bootstrapPython = Resolve-BootstrapPython -RootPath $projectRoot

if (-not (Test-Path ".venv")) {
  if ((Split-Path $bootstrapPython -Leaf) -ieq "py.exe") {
    & $bootstrapPython -3 -m venv .venv
  } else {
    & $bootstrapPython -m venv .venv
  }
}

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt
& $venvPython -m PyInstaller --noconfirm VirtualTV.spec

Copy-Item "tv_channels.json" "dist\\tv_channels.json" -Force

Write-Host "Build complete."
Write-Host "Executable: .\\dist\\VirtualTV.exe"
Write-Host "Channels:   .\\dist\\tv_channels.json"
