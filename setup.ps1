# Bootstrap development environments for all services
# Usage: .\setup.ps1
# Requirements: uv, node, npm

$ErrorActionPreference = "Stop"

function Setup-Python {
    param([string]$Service)
    Write-Host ""
    Write-Host "==> $Service" -ForegroundColor Cyan
    Push-Location $Service
    uv venv
    uv pip install -e ".[dev]" 
    Pop-Location
}

# Python services
Setup-Python "backend"
Setup-Python "bot"
Setup-Python "ml"

# Frontend
Write-Host ""
Write-Host "==> frontend" -ForegroundColor Cyan
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Push-Location frontend
    npm install
    Pop-Location
} else {
    Write-Host "npm not found - skipping." -ForegroundColor Yellow
    Write-Host "Install Node.js 20+ from https://nodejs.org/ and re-run." -ForegroundColor Yellow
}

# .env
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host ".env created from .env.example - fill in API keys." -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host ".env already exists, skipping." -ForegroundColor Gray
}

Write-Host ""
Write-Host "Done! Select Python interpreter in VS Code:" -ForegroundColor Green
Write-Host "  Ctrl+Shift+P -> Python: Select Interpreter -> backend\.venv\Scripts\python.exe" -ForegroundColor Gray
