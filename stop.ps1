# ScoreForge - Stop Services
Write-Host ""
Write-Host "=========================================="
Write-Host "  ScoreForge - Stop Services"
Write-Host "=========================================="
Write-Host ""

$ports = @(8000, 5173)
$found = $false

foreach ($port in $ports) {
    $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        $procId = $conn.OwningProcess
        Write-Host "  Stopping port $port (PID: $procId)..."

        # Kill entire process tree using taskkill (Stop-Process doesn't kill children)
        & taskkill /pid $procId /f /t 2>$null

        Start-Sleep -Milliseconds 500
        $stillListening = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if ($stillListening) {
            # Fallback: kill all python and node processes
            Write-Host "  Port still in use, force killing all related processes..."
            & taskkill /im python.exe /f /t 2>$null
            & taskkill /im node.exe /f /t 2>$null
            Start-Sleep -Milliseconds 500
        }
        Write-Host "  [OK]"
        $found = $true
    } else {
        Write-Host "  Port $port is not running"
    }
}

Write-Host ""
if ($found) {
    Write-Host "  Services stopped."
} else {
    Write-Host "  No services to stop."
}
Write-Host ""
Read-Host "Press Enter to exit"
