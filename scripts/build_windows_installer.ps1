$ErrorActionPreference = "Stop"
. (Join-Path (Split-Path -Parent $PSScriptRoot) "installer\installer_config.ps1")

function New-CleanDirectory {
  param(
    [string]$Path
  )

  if (Test-Path $Path) {
    Remove-Item $Path -Recurse -Force
  }
  New-Item -ItemType Directory -Path $Path -Force | Out-Null
}

function Resolve-Iscc {
  $candidates = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 7\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 7\ISCC.exe"
  )

  foreach ($candidate in $candidates) {
    if (Test-Path $candidate) {
      return $candidate
    }
  }

  throw "Inno Setup Compiler was not found. Install Inno Setup, then rerun this script."
}

$projectRoot = Split-Path -Parent $PSScriptRoot
$distDir = Join-Path $projectRoot "dist"
$appExe = Join-Path $distDir $ExecutableName
$channelsFile = Join-Path $distDir $ChannelsFileName
$brandingDir = Join-Path $projectRoot "assets\branding"

& (Join-Path $PSScriptRoot "generate_branding_assets.ps1")

if (-not (Test-Path $appExe)) {
  throw "Build the desktop app first. Missing: $appExe"
}
if (-not (Test-Path $channelsFile)) {
  throw "Missing channel list: $channelsFile"
}

$installerBuildDir = Join-Path $projectRoot "build\installer"
$stagingDir = Join-Path $installerBuildDir "staging"
$releaseDir = Join-Path $projectRoot "release"
$issPath = Join-Path $projectRoot "installer\AdamsyFreeTV.iss"
$outputInstaller = Join-Path $releaseDir ("Adamsy-Free-TV-Setup-" + $AppVersion + ".exe")

New-CleanDirectory -Path $stagingDir
New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null

$payloadFiles = @(
  @{ Source = $appExe; Target = $ExecutableName },
  @{ Source = $channelsFile; Target = $ChannelsFileName },
  @{ Source = (Join-Path $projectRoot $LauncherName); Target = $LauncherName },
  @{ Source = (Join-Path $projectRoot $StopLauncherName); Target = $StopLauncherName },
  @{ Source = (Join-Path $projectRoot "scripts\$StopScriptName"); Target = $StopScriptName },
  @{ Source = (Join-Path $projectRoot $ReadmeName); Target = $ReadmeName },
  @{ Source = (Join-Path $brandingDir "adamsy-free-tv.ico"); Target = "adamsy-free-tv.ico" },
  @{ Source = (Join-Path $brandingDir "adamsy-free-tv-wizard.png"); Target = "adamsy-free-tv-wizard.png" },
  @{ Source = (Join-Path $brandingDir "adamsy-free-tv-wizard-small.png"); Target = "adamsy-free-tv-wizard-small.png" }
)

foreach ($file in $payloadFiles) {
  if (-not (Test-Path $file.Source)) {
    throw "Missing payload file: $($file.Source)"
  }
  Copy-Item $file.Source (Join-Path $stagingDir $file.Target) -Force
}

if (-not (Test-Path $issPath)) {
  throw "Missing installer script: $issPath"
}

if (Test-Path $outputInstaller) {
  Remove-Item $outputInstaller -Force
}

$iscc = Resolve-Iscc
& $iscc `
  "/Qp" `
  "/DAppName=$AppName" `
  "/DAppVersion=$AppVersion" `
  "/DAppPublisher=$AppPublisher" `
  "/DStagingDir=$stagingDir" `
  "/DOutputDir=$releaseDir" `
  $issPath

if (-not (Test-Path $outputInstaller)) {
  throw "Installer build finished without creating $outputInstaller"
}

Write-Host "Installer build complete."
Write-Host "Output: $outputInstaller"
