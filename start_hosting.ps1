# Stop existing processes on ports
$ports = @(8000, 5173)
foreach ($port in $ports) {
    $pidProc = (Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Where-Object {$_.State -eq 'Listen'}).OwningProcess
    if ($pidProc) {
        Write-Host "Killing process $pidProc on port $port"
        Stop-Process -Id $pidProc -Force -ErrorAction SilentlyContinue
    }
}

# Start Backend
Write-Host "Starting Backend..."
$backend = Start-Process -FilePath "python" -ArgumentList "bridge.py" -WorkingDirectory "C:\Code\NotebooklmCrawler" -RedirectStandardOutput "logs\bridge.log" -RedirectStandardError "logs\bridge_err.log" -PassThru -WindowStyle Hidden

# Start Frontend
Write-Host "Starting Frontend..."
$frontend = Start-Process -FilePath "npm" -ArgumentList "run dev" -WorkingDirectory "C:\Code\NotebooklmCrawler\frontend" -RedirectStandardOutput "..\logs\frontend.log" -RedirectStandardError "..\logs\frontend_err.log" -PassThru -WindowStyle Hidden

Write-Host "Services Started."
Write-Host "Backend PID: $($backend.Id)"
Write-Host "Frontend PID: $($frontend.Id)"
Write-Host "Access at http://localhost:5173"
