$ErrorActionPreference = 'Stop'
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

Write-Host '============================================' -ForegroundColor Cyan
Write-Host ' PROBASHI BONDHU - FINAL COMPILE + GIT PUSH' -ForegroundColor Cyan
Write-Host '============================================' -ForegroundColor Cyan
Write-Host ''

$Project = $PSScriptRoot
Set-Location $Project

if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'Git পাওয়া যায়নি। Git install করে আবার চালান।'
}

$Python = $null
if (Test-Path (Join-Path $Project '.venv\Scripts\python.exe')) {
    $Python = Join-Path $Project '.venv\Scripts\python.exe'
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $Python = 'py'
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $Python = 'python'
} else {
    throw 'Python পাওয়া যায়নি।'
}

if (!(Test-Path (Join-Path $Project 'server.py'))) { throw 'server.py পাওয়া যায়নি।' }
if (!(Test-Path (Join-Path $Project 'landing\index.html'))) { throw 'landing\index.html পাওয়া যায়নি।' }
if (!(Test-Path (Join-Path $Project 'user\index.html'))) { throw 'user\index.html পাওয়া যায়নি।' }

Write-Host '1/5  Python compile check...' -ForegroundColor Cyan
& $Python -m py_compile (Join-Path $Project 'server.py')
if ($LASTEXITCODE -ne 0) { throw 'server.py compile failed.' }
Write-Host '      COMPILE: SUCCESS' -ForegroundColor Green

Write-Host '2/5  Initializing Git...' -ForegroundColor Cyan
if (!(Test-Path '.git')) { git init }
git branch -M main

$RemoteUrl = 'https://github.com/cwrm111-crypto/bangladesh-bank.git'
$remote = (git remote get-url origin 2>$null)
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($remote)) {
    git remote add origin $RemoteUrl
} elseif ($remote.Trim() -ne $RemoteUrl) {
    git remote set-url origin $RemoteUrl
}

Write-Host '3/5  Staging final source...' -ForegroundColor Cyan
git add .

$pending = git status --porcelain
if ($pending) {
    git commit -m 'Publish final landing, auth and connected app'
}

Write-Host '4/5  Syncing GitHub main...' -ForegroundColor Cyan
git fetch origin
if ($LASTEXITCODE -ne 0) { throw 'git fetch failed.' }

$remoteBranchExists = git branch -r --list 'origin/main'
if ($remoteBranchExists) {
    git pull --no-rebase --allow-unrelated-histories --no-edit
    if ($LASTEXITCODE -ne 0) {
        $conflicts = @(git diff --name-only --diff-filter=U)
        if ($conflicts.Count -eq 0) { throw 'Git merge failed.' }
        Write-Host '      Resolving bootstrap conflicts with LOCAL final files...' -ForegroundColor Yellow
        foreach ($file in $conflicts) {
            git checkout --ours -- $file
            git add -- $file
        }
        git commit -m 'Resolve GitHub bootstrap merge'
    }
}

Write-Host '5/5  Pushing to GitHub...' -ForegroundColor Cyan
git push -u origin main
if ($LASTEXITCODE -ne 0) { throw 'GitHub push failed.' }

Write-Host ''
Write-Host '============================================' -ForegroundColor Green
Write-Host ' FINAL COMPILE + GIT PUSH: SUCCESS' -ForegroundColor Green
Write-Host '============================================' -ForegroundColor Green
Write-Host 'GitHub: https://github.com/cwrm111-crypto/bangladesh-bank' -ForegroundColor Green
Write-Host ''
Write-Host 'Main files:' -ForegroundColor White
Write-Host '  landing\index.html'
Write-Host '  user\index.html'
Write-Host '  server.py'
Write-Host '  app.py'
Write-Host '  requirements.txt'
Write-Host ''
