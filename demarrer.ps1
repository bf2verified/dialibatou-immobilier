# =====================================================================
#  DIALIBATOU BTP IMMOBILIER - Lanceur one-click (Windows PowerShell)
#  .\demarrer.ps1          -> seed + API (8001) + site (5500) + tests
#  .\demarrer.ps1 -SansTests  -> idem sans lancer backend_test.py
#  .\arreter.ps1           -> arrete les processus 8001 / 5500
# =====================================================================
param([switch]$SansTests)
$ErrorActionPreference = "Stop"

$root    = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "dialibatou-backend"
$py      = Join-Path $backend "venv\Scripts\python.exe"

if (-not (Test-Path $py)) {
    Write-Host "✗ Environnement Python introuvable." -ForegroundColor Red
    Write-Host "  cd dialibatou-backend; python -m venv venv; venv\Scripts\activate; pip install -r requirements.txt"
    exit 1
}

Write-Host "1/4 Seed de la base PostgreSQL (dialibatou_db)..." -ForegroundColor Cyan
& $py (Join-Path $backend "seed.py")

Write-Host "2/4 Demarrage de l'API FastAPI (port 8001)..." -ForegroundColor Cyan
Start-Process $py -ArgumentList "-m", "uvicorn", "main:app", "--port", "8001" `
    -WorkingDirectory $backend -WindowStyle Hidden

Write-Host "3/4 Demarrage du site statique (port 5500)..." -ForegroundColor Cyan
Start-Process python -ArgumentList "-m", "http.server", "5500" `
    -WorkingDirectory $root -WindowStyle Hidden

Start-Sleep -Seconds 6
try {
    $health = Invoke-RestMethod http://localhost:8001/api/health
    Write-Host "    API en ligne : $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "    ✗ L'API ne repond pas sur 8001" -ForegroundColor Red
}

if (-not $SansTests) {
    Write-Host "4/4 Tests d'integration..." -ForegroundColor Cyan
    & $py (Join-Path $root "backend_test.py")
} else {
    Write-Host "4/4 Tests ignores (-SansTests)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "  Site  : http://localhost:5500" -ForegroundColor Green
Write-Host "  Admin : http://localhost:5500  (bouton 'Espace Administration' en bas de page)" -ForegroundColor Green
Write-Host "  Swagger / pgAdmin : http://localhost:8001/docs" -ForegroundColor Green
Write-Host "  Arret : .\arreter.ps1"
