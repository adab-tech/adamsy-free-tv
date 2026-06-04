param(
  [switch]$AddToStartup
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$launcher = Join-Path $projectRoot "start_tv_app.bat"
if (-not (Test-Path $launcher)) {
  throw "Launcher not found: $launcher"
}

$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Adamsy Free TV.lnk"
$iconCandidates = @(
  (Join-Path $projectRoot "dist\VirtualTV.exe"),
  (Join-Path $projectRoot "assets\branding\adamsy-free-tv.ico"),
  "C:\Program Files\VideoLAN\VLC\vlc.exe"
)

$iconLocation = $null
foreach ($candidate in $iconCandidates) {
  if (Test-Path $candidate) {
    $iconLocation = "$candidate,0"
    break
  }
}

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $launcher
$shortcut.WorkingDirectory = $projectRoot
if ($iconLocation) {
  $shortcut.IconLocation = $iconLocation
}
$shortcut.Description = "Launch Adamsy Free TV"
$shortcut.Save()

Write-Host "Desktop shortcut created: $shortcutPath"

if ($AddToStartup) {
  $startup = [Environment]::GetFolderPath("Startup")
  $startupShortcut = Join-Path $startup "Adamsy Free TV.lnk"
  Copy-Item -Path $shortcutPath -Destination $startupShortcut -Force
  Write-Host "Startup shortcut created: $startupShortcut"
}
