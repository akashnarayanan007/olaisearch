#!/usr/bin/env pwsh
# PowerShell equivalents for Makefile commands
# Usage: ./build.ps1 <target>
# Targets: dev, test, lint, type-check, eval, install, clean

param(
    [Parameter(Mandatory=$true)]
    [string]$Target
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

function Run-Test {
    Write-Host "Running tests..." -ForegroundColor Cyan
    Set-Location $ProjectRoot
    python -m pytest tests/ -v --timeout=60
}

function Run-Lint {
    Write-Host "Running linters..." -ForegroundColor Cyan
    Set-Location $ProjectRoot
    python -m ruff check backend/ tests/ eval/
    python -m black --check backend/ tests/ eval/
}

function Run-TypeCheck {
    Write-Host "Running type checker..." -ForegroundColor Cyan
    Set-Location $ProjectRoot
    python -m mypy backend/ tests/
}

function Start-Dev {
    Write-Host "Starting development services..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; python -m uvicorn backend.main:app --reload --port 8000"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot/frontend'; npm run dev"
    Write-Host "API: http://localhost:8000/docs" -ForegroundColor Green
    Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
}

function Run-Eval {
    Write-Host "Running evaluation scripts..." -ForegroundColor Cyan
    Set-Location $ProjectRoot
    python eval/scripts/eval_segmentation.py
    python eval/scripts/eval_recognition.py
    python eval/scripts/eval_retrieval.py
}

function Install-Deps {
    Write-Host "Installing dependencies..." -ForegroundColor Cyan
    Set-Location $ProjectRoot
    pip install -e ".[dev]"
    Set-Location "$ProjectRoot/frontend"
    npm install
}

function Clean {
    Write-Host "Cleaning build artifacts..." -ForegroundColor Yellow
    Set-Location $ProjectRoot
    Remove-Item -Recurse -Force __pycache__, backend/__pycache__, tests/__pycache__, frontend/node_modules, frontend/dist, *.db -ErrorAction SilentlyContinue
    Write-Host "Clean complete." -ForegroundColor Green
}

switch ($Target) {
    "test" { Run-Test }
    "lint" { Run-Lint }
    "type-check" { Run-TypeCheck }
    "dev" { Start-Dev }
    "eval" { Run-Eval }
    "install" { Install-Deps }
    "clean" { Clean }
    default {
        Write-Host "Usage: ./build.ps1 {test|lint|type-check|dev|eval|install|clean}" -ForegroundColor Red
        exit 1
    }
}
