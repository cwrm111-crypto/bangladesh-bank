$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " BANGLADESH BANK DEMO - FINAL PUBLISH" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

& "$PSScriptRoot\GITHUB-PUSH.ps1"
if ($LASTEXITCODE -ne 0) { throw "GitHub publish failed." }

& "$PSScriptRoot\VERCEL-DEPLOY.ps1"
if ($LASTEXITCODE -ne 0) { throw "Vercel deployment failed." }

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " FINAL PUBLISH FLOW COMPLETED" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
