@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Ambiente virtual nao encontrado em .venv\Scripts\python.exe
    echo Rode a instalacao inicial do projeto antes de usar este atalho.
    pause
    exit /b 1
)

where docker >nul 2>nul
if errorlevel 1 (
    echo Docker nao encontrado no PATH.
    echo Instale e abra o Docker Desktop antes de usar este atalho.
    pause
    exit /b 1
)

docker version >nul 2>nul
if errorlevel 1 (
    echo O Docker Desktop parece instalado, mas o daemon nao esta acessivel.
    echo Abra o Docker Desktop e espere ele terminar de iniciar.
    pause
    exit /b 1
)

echo Subindo PostgreSQL com pgvector...
docker compose up -d postgres
if errorlevel 1 (
    echo Falha ao subir o banco com Docker Compose.
    pause
    exit /b 1
)

echo Abrindo documentacao da API...
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 6; Start-Process 'http://127.0.0.1:8010/docs'"

echo Subindo API em http://127.0.0.1:8010 ...
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
