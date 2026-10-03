@echo off
setlocal
cd /d "%~dp0"
where powershell >nul 2>&1 || (
  echo Windows PowerShell was not found.
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0FINAL-ONE-CLICK-DEPLOY.ps1"
pause
