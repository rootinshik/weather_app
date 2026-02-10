# Bootstrap development environments for all services
# Usage: .\setup.ps1
# Requirements: uv, node, npm

$ErrorActionPreference = "Stop"

function Setup-Python {
    param([string]$Service)
    Write-Host "`n==> $Service" -ForegroundColor Cyan
    Push-Location $Service
    uv venv
    uv pip install -e .
    Pop-Location
}

# Python services
Setup-Python "backend"
Setup-Python "bot"
Setup-Python "ml"

# Frontend
Write-Host "`n==> frontend" -ForegroundColor Cyan
Push-Location frontend
npm install
Pop-Location

# .env
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "`n.env создан из .env.example — заполни API-ключи." -ForegroundColor Yellow
} else {
    Write-Host "`n.env уже существует, пропускаем." -ForegroundColor Gray
}

Write-Host "`nГотово! Теперь выбери интерпретатор в VS Code:" -ForegroundColor Green
Write-Host "  Ctrl+Shift+P -> Python: Select Interpreter -> backend\.venv\Scripts\python.exe" -ForegroundColor Gray
