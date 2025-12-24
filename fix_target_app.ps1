#!/usr/bin/env pwsh
# Complete Target App Fix and Restart

Write-Host "===== Target App Complete Fix =====" -ForegroundColor Cyan

# 1. Kill existing Target App
Write-Host "`n[1] Terminating existing Target App..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.CommandLine -like '*target_app*'} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# 2. Kill port 8000 if still occupied
$conn = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($conn) {
    Stop-Process -Id $conn.OwningProcess -Force
    Write-Host "Port 8000 freed." -ForegroundColor Green
}

# 3. Start Target App in new window
Write-Host "`n[2] Starting Target App with fixed assignment logging..." -ForegroundColor Yellow
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "python target_app/main.py"

Write-Host "`n✅ Target App restarted!" -ForegroundColor Green
Write-Host "Watch the new terminal for [INFO] log messages." -ForegroundColor Yellow
