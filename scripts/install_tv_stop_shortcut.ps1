$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$stopLauncher = Join-Path $projectRoot "stop_tv_app.bat"
if (-not (Test-Path $stopLauncher)) {
  throw "Stop launcher not found: $stopLauncher"
}

$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Stop Adamsy Free TV.lnk"

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $stopLauncher
$shortcut.WorkingDirectory = $projectRoot
$shortcut.IconLocation = "%SystemRoot%\System32\SHELL32.dll,27"
$shortcut.Description = "Stop Adamsy Free TV"
$shortcut.Save()

Write-Host "Desktop stop shortcut created: $shortcutPath"
