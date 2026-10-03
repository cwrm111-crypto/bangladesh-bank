$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

if (!(Test-Path ".venv")) {
    py -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt

$env:ADMIN_USER = "admin"
$env:ADMIN_PASSWORD = "ChangeMe-123!"
$env:SECRET_KEY = "ProbashiBondhu-Demo-Change-Me"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " BANGLADESH BANK STYLED — DEMO" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "LANDING: http://127.0.0.1:8080/" -ForegroundColor Green
Write-Host "APP    : http://127.0.0.1:8080/app" -ForegroundColor Green
Write-Host "ADMIN  : http://127.0.0.1:8080/admin" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Start-Process "http://127.0.0.1:8080/"
& ".\.venv\Scripts\python.exe" server.py
