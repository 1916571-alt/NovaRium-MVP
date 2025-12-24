#!/usr/bin/env pwsh
# Target App 강제 재시작 스크립트

Write-Host "===== Target App Restart Script =====" -ForegroundColor Cyan

# 1. Find process using port 8000
Write-Host "`n[1] Checking port 8000..." -ForegroundColor Yellow
$conn = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($conn) {
    $pid = $conn.OwningProcess
    Write-Host "Found process PID: $pid" -ForegroundColor Green
    
    # 2. Kill the process
    Write-Host "`n[2] Terminating process..." -ForegroundColor Yellow
    Stop-Process -Id $pid -Force
    Write-Host "Process terminated." -ForegroundColor Green
    Start-Sleep -Seconds 1
} else {
    Write-Host "No process found on port 8000." -ForegroundColor Gray
}

# 3. Restart Target App
Write-Host "`n[3] Starting Target App..." -ForegroundColor Yellow
Write-Host "Running: python target_app/main.py" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Gray

# Start in new window to see logs
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "python target_app/main.py"

Write-Host "`nTarget App started in new window!" -ForegroundColor Green
Write-Host "Check the new terminal for [INFO] log messages." -ForegroundColor Yellow
