# =====================================================================
#  Arrete les processus lances par demarrer.ps1 (ports 8001 et 5500)
# =====================================================================
$ErrorActionPreference = "SilentlyContinue"

foreach ($port in 8001, 5500) {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen
    foreach ($c in $conns) {
        $proc = Get-Process -Id $c.OwningProcess
        if ($proc.ProcessName -match 'python') {
            Stop-Process -Id $proc.Id -Force
            Write-Host "Arrete : $($proc.ProcessName) (PID $($proc.Id)) sur le port $port" -ForegroundColor Yellow
        }
    }
}
Write-Host "Termine." -ForegroundColor Green
