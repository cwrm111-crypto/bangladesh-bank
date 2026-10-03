$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " BANGLADESH BANK DEMO - VERCEL FLASK DEPLOY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

if (!(Test-Path "app.py")) { throw "app.py is missing." }
if (!(Test-Path "server.py")) { throw "server.py is missing." }
if (!(Test-Path "requirements.txt")) { throw "requirements.txt is missing." }

if (Get-Command py -ErrorAction SilentlyContinue) {
  py -m py_compile server.py
  if ($LASTEXITCODE -ne 0) { throw "server.py compile check failed." }
}

if (!(Get-Command node -ErrorAction SilentlyContinue)) { throw "Node.js is required for Vercel CLI." }
if (!(Get-Command npm -ErrorAction SilentlyContinue)) { throw "npm is required for Vercel CLI." }

if (!(Get-Command vercel -ErrorAction SilentlyContinue)) {
  npm install -g vercel
}
if (!(Get-Command vercel -ErrorAction SilentlyContinue)) { throw "Vercel CLI installation failed." }

& vercel whoami 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Vercel login required..." -ForegroundColor Yellow
  vercel login
  if ($LASTEXITCODE -ne 0) { throw "Vercel login failed." }
}

# Remove stale project metadata from the previous Next.js project.
if (Test-Path ".vercel") {
  Remove-Item ".vercel" -Recurse -Force
  Write-Host "Removed old .vercel link." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Deploying this folder as a fresh Flask/Python project..." -ForegroundColor Green
vercel --prod --yes
if ($LASTEXITCODE -ne 0) { throw "Vercel deployment failed." }

Write-Host ""
Write-Host "VERCEL DEPLOY: COMMAND COMPLETED" -ForegroundColor Green
Write-Host "Use the Production URL printed by Vercel." -ForegroundColor Green
