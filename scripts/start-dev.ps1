$ErrorActionPreference = "Stop"

Write-Host "Subindo PostgreSQL com pgvector via Docker Compose..."
docker compose up -d postgres

Write-Host "Aguardando banco ficar saudavel..."
for ($i = 0; $i -lt 30; $i++) {
    $status = docker inspect --format "{{.State.Health.Status}}" assistente-contabil-postgres 2>$null
    if ($status -eq "healthy") {
        break
    }
    Start-Sleep -Seconds 2
}

if (Test-Path ".\frontend\package.json") {
    if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
        Write-Host "[AVISO] npm.cmd nao encontrado. O frontend React nao sera iniciado."
    }
    elseif (-not (Test-Path ".\frontend\node_modules")) {
        Write-Host "[AVISO] frontend\node_modules nao encontrado. Rode: cd frontend ; npm.cmd install"
    }
    else {
        Write-Host "Subindo frontend React em http://127.0.0.1:5173 ..."
        $frontendPath = Join-Path $PWD "frontend"
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$frontendPath'; npm.cmd run dev"
    }
}

Write-Host "Subindo API FastAPI..."
& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8010 --reload
