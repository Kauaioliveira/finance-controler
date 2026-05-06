$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..\\frontend")

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    Write-Host "npm.cmd nao encontrado. Instale Node.js antes de continuar."
    exit 1
}

if (-not (Test-Path "node_modules")) {
    Write-Host "Dependencias do frontend ainda nao instaladas."
    Write-Host "Rode: cd frontend ; npm.cmd install"
    exit 1
}

Write-Host "Subindo frontend React..."
& npm.cmd run dev
