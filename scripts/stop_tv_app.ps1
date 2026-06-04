$ErrorActionPreference = "Stop"

$stopped = @()

# Stop packaged app if present.
Get-Process -Name "VirtualTV" -ErrorAction SilentlyContinue | ForEach-Object {
  Stop-Process -Id $_.Id -Force
  $stopped += "VirtualTV.exe (PID $($_.Id))"
}

# Stop python instances that launched tv_main.py.
Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" |
  Where-Object { $_.CommandLine -like "*tv_main.py*" } |
  ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force
    $stopped += "$($_.Name) (PID $($_.ProcessId))"
  }

if ($stopped.Count -eq 0) {
  Write-Host "No running TV app process was found."
} else {
  Write-Host "Stopped TV app process(es):"
  $stopped | ForEach-Object { Write-Host "  - $_" }
}
