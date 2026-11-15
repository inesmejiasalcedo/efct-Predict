# Abre el backend y el frontend en dos ventanas de PowerShell.
# Uso (desde la carpeta efct-predict-v2):  .\start.ps1
# Requiere haber hecho una vez la instalacion descrita en README.md.

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path "$root\backend\.env")) {
    Write-Host "Falta backend\.env. Copia backend\.env.example como backend\.env y completalo." -ForegroundColor Yellow
    exit 1
}

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev"

Write-Host "Backend:  http://127.0.0.1:8000"
Write-Host "Frontend: http://localhost:5173"
