$ErrorActionPreference = 'Stop'
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

Write-Host ''
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ' PROBASHI BONDHU - FINAL BUILD + GITHUB + VERCEL' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ''

$Project = $PSScriptRoot
Set-Location $Project

function Need-Command {
    param([string]$Name,[string]$Hint)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name not found. $Hint"
    }
}

function Run-Checked {
    param([string]$FilePath,[string[]]$Arguments,[string]$ErrorMessage)
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) { throw $ErrorMessage }
}

Write-Host '[1/7] Checking project files...' -ForegroundColor Cyan
$required = @('app.py','server.py','requirements.txt','landing\index.html','user\index.html','vercel.json')
foreach ($f in $required) {
    if (-not (Test-Path (Join-Path $Project $f))) { throw "Missing required file: $f" }
}
Write-Host '      SOURCE: OK' -ForegroundColor Green

Write-Host '[2/7] Preparing Python environment...' -ForegroundColor Cyan
Need-Command 'py' 'Install Python 3 and run this script again.'
$Venv = Join-Path $Project '.venv'
$Python = Join-Path $Venv 'Scripts\python.exe'
if (-not (Test-Path $Python)) {
    Write-Host '      Creating .venv...' -ForegroundColor Yellow
    Run-Checked 'py' @('-3','-m','venv',$Venv) 'Virtual environment creation failed.'
}
Run-Checked $Python @('-m','pip','install','-r',(Join-Path $Project 'requirements.txt')) 'Dependency installation failed.'
Run-Checked $Python @('-m','py_compile',(Join-Path $Project 'server.py')) 'server.py compile failed.'
$env:SECRET_KEY = if ($env:SECRET_KEY) { $env:SECRET_KEY } else { 'ProbashiBondhu-Demo-Secret-Change-This' }
$env:ADMIN_USER = if ($env:ADMIN_USER) { $env:ADMIN_USER } else { 'admin' }
$env:ADMIN_PASSWORD = if ($env:ADMIN_PASSWORD) { $env:ADMIN_PASSWORD } else { 'ChangeMe-123!' }
& $Python -c "import server; print('IMPORT_OK')"
if ($LASTEXITCODE -ne 0) { throw 'Flask application import failed.' }
Write-Host '      PYTHON COMPILE: SUCCESS' -ForegroundColor Green
Write-Host '      FLASK IMPORT: SUCCESS' -ForegroundColor Green

Write-Host '[3/7] Publishing to GitHub...' -ForegroundColor Cyan
Need-Command 'git' 'Install Git for Windows and run this script again.'
$RepoUrl = 'https://github.com/cwrm111-crypto/bangladesh-bank.git'
if (-not (Test-Path (Join-Path $Project '.git'))) { Run-Checked 'git' @('init') 'git init failed.' }
Run-Checked 'git' @('branch','-M','main') 'Could not set main branch.'
$remoteUrl = ''
try { $remoteUrl = (git remote get-url origin 2>$null).Trim() } catch { $remoteUrl = '' }
if ([string]::IsNullOrWhiteSpace($remoteUrl)) {
    Run-Checked 'git' @('remote','add','origin',$RepoUrl) 'Could not add GitHub origin.'
} elseif ($remoteUrl -ne $RepoUrl) {
    Run-Checked 'git' @('remote','set-url','origin',$RepoUrl) 'Could not update GitHub origin.'
}
Run-Checked 'git' @('add','.') 'git add failed.'
$status = @(git status --porcelain)
if ($status.Count -gt 0) { Run-Checked 'git' @('commit','-m','Final landing auth app release') 'git commit failed.' }
Run-Checked 'git' @('fetch','origin') 'git fetch failed.'
$remoteMainExists = @(git branch -r --list 'origin/main').Count -gt 0
if ($remoteMainExists) {
    git merge origin/main --no-rebase --allow-unrelated-histories --no-edit
    if ($LASTEXITCODE -ne 0) {
        $conflicts = @(git diff --name-only --diff-filter=U)
        if ($conflicts.Count -eq 0) { throw 'Git merge failed.' }
        Write-Host '      Resolving merge conflicts using local files...' -ForegroundColor Yellow
        foreach ($f in $conflicts) {
            git checkout --ours -- $f
            if ($LASTEXITCODE -ne 0) { throw "Could not resolve $f" }
            git add -- $f
            if ($LASTEXITCODE -ne 0) { throw "Could not stage $f" }
        }
        Run-Checked 'git' @('commit','-m','Resolve GitHub bootstrap merge') 'Merge commit failed.'
    }
}
Run-Checked 'git' @('push','-u','origin','main') 'GitHub push failed.'
Write-Host '      GITHUB PUSH: SUCCESS' -ForegroundColor Green

Write-Host '[4/7] Checking Vercel CLI...' -ForegroundColor Cyan
Need-Command 'node' 'Install Node.js and run this script again.'
Need-Command 'npm' 'Install Node.js and run this script again.'
if (-not (Get-Command vercel -ErrorAction SilentlyContinue)) {
    npm install -g vercel
    if ($LASTEXITCODE -ne 0) { throw 'Vercel CLI install failed.' }
}
Write-Host '      VERCEL CLI: OK' -ForegroundColor Green

Write-Host '[5/7] Checking Vercel login...' -ForegroundColor Cyan
vercel whoami > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host '      Vercel login required. Follow the Vercel login flow.' -ForegroundColor Yellow
    vercel login
    if ($LASTEXITCODE -ne 0) { throw 'Vercel login failed.' }
}
Write-Host '      VERCEL LOGIN: OK' -ForegroundColor Green

Write-Host '[6/7] Configuring dedicated Vercel project...' -ForegroundColor Cyan
$VercelProject = 'bangladesh-bank-demo'
$vercelDir = Join-Path $Project '.vercel'
if (Test-Path $vercelDir) { Remove-Item $vercelDir -Recurse -Force }
vercel project inspect $VercelProject > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "      Creating project: $VercelProject" -ForegroundColor Yellow
    vercel project add $VercelProject
    if ($LASTEXITCODE -ne 0) { throw 'Vercel project creation failed.' }
}
vercel link --yes --project $VercelProject
if ($LASTEXITCODE -ne 0) { throw 'Vercel project link failed.' }
Write-Host '      VERCEL PROJECT: READY' -ForegroundColor Green

Write-Host '[7/7] Deploying to Vercel production...' -ForegroundColor Cyan
vercel deploy --prod --yes --project $VercelProject
if ($LASTEXITCODE -ne 0) { throw 'Vercel production deployment failed.' }

Write-Host ''
Write-Host '============================================================' -ForegroundColor Green
Write-Host ' FINAL BUILD + GITHUB PUSH + VERCEL DEPLOY: SUCCESS' -ForegroundColor Green
Write-Host '============================================================' -ForegroundColor Green
Write-Host 'GitHub: https://github.com/cwrm111-crypto/bangladesh-bank' -ForegroundColor Green
Write-Host 'Vercel Project: bangladesh-bank-demo' -ForegroundColor Green
Write-Host 'Local: http://127.0.0.1:8080/' -ForegroundColor Green
Write-Host ''
