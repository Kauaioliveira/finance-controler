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

Write-Host "Subindo API FastAPI..."
& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
