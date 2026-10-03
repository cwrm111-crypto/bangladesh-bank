$ErrorActionPreference="Stop"
Set-Location $PSScriptRoot

if (!(Get-Command py -ErrorAction SilentlyContinue)) {
  throw "Python launcher 'py' was not found. Install Python 3.11+ first."
}

if (!(Test-Path ".venv")) { py -m venv .venv }

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt

$env:ADMIN_USER="admin"
$env:ADMIN_PASSWORD="ChangeMe-123!"
$env:SECRET_KEY="CHANGE-ME-THIS-DEMO-SECRET"

# Ensure the database tables exist before the server starts.
& ".\.venv\Scripts\python.exe" -c "import server; server.ensure_db(); print('DATABASE: READY')"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "      PROBASHI BONDHU - PROFESSIONAL DEMO" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "USER : http://127.0.0.1:8080/" -ForegroundColor Green
Write-Host "ADMIN: http://127.0.0.1:8080/admin" -ForegroundColor Yellow
Write-Host "ADMIN USER: admin" -ForegroundColor Yellow
Write-Host "ADMIN PASS: ChangeMe-123!" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Start-Process "http://127.0.0.1:8080/"
& ".\.venv\Scripts\python.exe" server.py
