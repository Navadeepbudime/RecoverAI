$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

Start-Process -FilePath (Join-Path $backend ".venv\Scripts\python.exe") -ArgumentList "run.py" -WorkingDirectory $backend -WindowStyle Hidden
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $frontend "start-dev.ps1") -WorkingDirectory $frontend

Write-Host "RecoverAI is starting."
Write-Host "Backend:  http://localhost:5000/api/health"
Write-Host "Frontend: http://localhost:5173"
