# scripts/run_final_benchmark.ps1 — PowerShell launcher for PolyFlow Final Benchmark Runner

$RepoRoot = Split-Path -Parent $PSScriptRoot
Write-Host "Running PolyFlow Final Benchmark and Anti-Fabrication Verification..." -ForegroundColor Cyan
python "$RepoRoot/scripts/run_final_benchmark.py"
