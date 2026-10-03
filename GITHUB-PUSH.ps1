$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

$Owner = "cwrm111-crypto"
$RepoName = "bangladesh-bank"
$Repo = "$Owner/$RepoName"
$Remote = "https://github.com/$Repo.git"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " BANGLADESH BANK DEMO - GITHUB PUBLISH" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

if (!(Get-Command git -ErrorAction SilentlyContinue)) { throw "Git is not installed." }

if (!(Test-Path ".git")) { git init }
git branch -M main

if (!(Get-Command gh -ErrorAction SilentlyContinue)) {
  if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Host "Installing GitHub CLI..." -ForegroundColor Yellow
    winget install --id GitHub.cli --source winget --accept-package-agreements --accept-source-agreements
  }
}

if (!(Get-Command gh -ErrorAction SilentlyContinue)) {
  $candidates = @(
    (Join-Path $env:ProgramFiles "GitHub CLI\gh.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\GitHub CLI\gh.exe")
  ) | Where-Object { Test-Path $_ }
  if ($candidates.Count -gt 0) {
    $env:Path = "$(Split-Path $candidates[0] -Parent);$env:Path"
  }
}

if (!(Get-Command gh -ErrorAction SilentlyContinue)) {
  throw "GitHub CLI (gh) is required."
}

& gh auth status 2>$null
if ($LASTEXITCODE -ne 0) {
  & gh auth login --web --git-protocol https
  if ($LASTEXITCODE -ne 0) { throw "GitHub authentication failed." }
}

# Make sure the required repository exists.
& gh repo view $Repo --json nameWithOwner -q .nameWithOwner 2>$null
$exists = ($LASTEXITCODE -eq 0)

$originNames = @(git remote 2>$null)
if ($originNames -contains "origin") { git remote remove origin }
git remote add origin $Remote

git add .
if (git status --porcelain) {
  git commit -m "Publish connected landing, auth and app flow"
}

if (!$exists) {
  Write-Host "Creating public repository $Repo ..." -ForegroundColor Yellow
  & gh repo create $Repo --public --source=. --remote=origin --push
  if ($LASTEXITCODE -ne 0) { throw "GitHub repository creation/push failed." }
}
else {
  Write-Host "Repository exists. Syncing remote main..." -ForegroundColor Green
  git fetch origin
  if ($LASTEXITCODE -ne 0) { throw "git fetch failed." }

  git pull --no-rebase --allow-unrelated-histories --no-edit
  if ($LASTEXITCODE -ne 0) {
    $conflicts = @(git diff --name-only --diff-filter=U)
    if ($conflicts.Count -eq 0) {
      throw "Git merge failed for a reason other than a file conflict."
    }
    Write-Host "Resolving repository bootstrap conflicts in favor of local project files..." -ForegroundColor Yellow
    foreach ($f in $conflicts) {
      git checkout --ours -- $f
      git add -- $f
    }
    git commit -m "Resolve repository bootstrap merge"
    if ($LASTEXITCODE -ne 0) { throw "Conflict resolution commit failed." }
  }

  git push -u origin main
  if ($LASTEXITCODE -ne 0) { throw "GitHub push failed." }
}

Write-Host ""
Write-Host "GITHUB PUBLISH: SUCCESS" -ForegroundColor Green
Write-Host "https://github.com/$Repo" -ForegroundColor Green
