param(
  [string]$Day = "SUN",
  [string]$Time = "09:00"
)

$ErrorActionPreference = "Stop"

function Resolve-PythonExecutable {
  param(
    [string]$RootPath
  )

  $candidates = @(
    (Join-Path $RootPath ".venv\Scripts\python.exe"),
    "python"
  )

  foreach ($candidate in $candidates) {
    if ($candidate -eq "python") {
      $cmd = Get-Command python -ErrorAction SilentlyContinue
      if ($cmd) {
        return $cmd.Source
      }
    } elseif (Test-Path $candidate) {
      return $candidate
    }
  }

  $installedPython = Get-ChildItem "$env:LOCALAPPDATA\Programs\Python" -Directory -ErrorAction SilentlyContinue |
    Sort-Object Name -Descending |
    ForEach-Object { Join-Path $_.FullName "python.exe" } |
    Where-Object { Test-Path $_ } |
    Select-Object -First 1
  if ($installedPython) {
    return $installedPython
  }

  return $null
}

function Resolve-UpdateCommand {
  param(
    [string]$RootPath
  )

  $packagedExe = Join-Path $RootPath "dist\VirtualTV.exe"
  if (Test-Path $packagedExe) {
    return @{
      Execute = $packagedExe
      Argument = "--refresh-channels --limit 700 --verify-live --verify-count 2400 --verify-timeout 2 --verify-workers 32"
      WorkingDirectory = Split-Path -Parent $packagedExe
    }
  }

  $updater = Join-Path $RootPath "tv_updater.py"
  if (-not (Test-Path $updater)) {
    throw "Updater not found: $updater"
  }

  $pythonExe = Resolve-PythonExecutable -RootPath $RootPath
  if (-not $pythonExe) {
    throw "Could not find Python executable."
  }

  return @{
    Execute = $pythonExe
    Argument = "`"$updater`" --limit 700 --verify-live --verify-count 2400 --verify-timeout 2 --verify-workers 32"
    WorkingDirectory = $RootPath
  }
}

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$updateCommand = Resolve-UpdateCommand -RootPath $projectRoot

$taskName = "Adamsy Free TV Weekly Channel Refresh"
$weeklyDays = @{
  "MON" = "Monday"
  "TUE" = "Tuesday"
  "WED" = "Wednesday"
  "THU" = "Thursday"
  "FRI" = "Friday"
  "SAT" = "Saturday"
  "SUN" = "Sunday"
}

$dayToken = $Day.Trim().ToUpperInvariant()
if (-not $weeklyDays.ContainsKey($dayToken)) {
  throw "Invalid day '$Day'. Use one of: MON, TUE, WED, THU, FRI, SAT, SUN."
}

$startDateTime = [datetime]::ParseExact($Time, "HH:mm", $null)
$action = New-ScheduledTaskAction `
  -Execute $updateCommand.Execute `
  -Argument $updateCommand.Argument `
  -WorkingDirectory $updateCommand.WorkingDirectory
$trigger = New-ScheduledTaskTrigger -Weekly -WeeksInterval 1 -DaysOfWeek $weeklyDays[$dayToken] -At $startDateTime
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable

$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
  Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Weekly Adamsy Free TV channel refresh" | Out-Null
Write-Host "Scheduled task created/updated: $taskName"
Write-Host "Runs: weekly on $Day at $Time"
