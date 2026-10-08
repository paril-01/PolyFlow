# scripts/run_showcase.ps1 — PowerShell launcher for PolyFlow Showcase Server

$RepoRoot = Split-Path -Parent $PSScriptRoot
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "STARTING POLYFLOW EVIDENCE & SHOWCASE SERVER" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Host: 127.0.0.1 | Port: 8000"
Write-Host "Open browser at: http://127.0.0.1:8000"

python -m uvicorn showcase_app.backend.app:app --host 127.0.0.1 --port 8000 --reload
