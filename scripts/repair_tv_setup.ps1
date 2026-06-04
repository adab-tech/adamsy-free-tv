param(
  [string]$Day = "SUN",
  [string]$Time = "09:00"
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$desktop = [Environment]::GetFolderPath("Desktop")
$startup = [Environment]::GetFolderPath("Startup")
$legacyDesktopShortcut = Join-Path $desktop "Live TV App.lnk"
$legacyStartupShortcut = Join-Path $startup "Live TV App.lnk"
$legacyStopShortcut = Join-Path $desktop "Stop Live TV App.lnk"
if (Test-Path $legacyDesktopShortcut) { Remove-Item $legacyDesktopShortcut -Force }
if (Test-Path $legacyStartupShortcut) { Remove-Item $legacyStartupShortcut -Force }
if (Test-Path $legacyStopShortcut) { Remove-Item $legacyStopShortcut -Force }

Write-Host "Recreating launch shortcuts..."
& (Join-Path $scriptDir "install_tv_shortcut.ps1") -AddToStartup

Write-Host "Recreating stop shortcut..."
& (Join-Path $scriptDir "install_tv_stop_shortcut.ps1")

Write-Host "Recreating weekly refresh scheduled task..."
& (Join-Path $scriptDir "register_tv_weekly_update.ps1") -Day $Day -Time $Time

Write-Host "Repair completed successfully."
