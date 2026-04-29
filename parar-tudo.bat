@echo off
setlocal

cd /d "%~dp0"

where docker >nul 2>nul
if errorlevel 1 (
    echo Docker nao encontrado no PATH.
    pause
    exit /b 1
)

docker version >nul 2>nul
if errorlevel 1 (
    echo O daemon do Docker nao esta acessivel.
    echo Abra o Docker Desktop antes de usar este atalho.
    pause
    exit /b 1
)

echo Derrubando containers do projeto...
docker compose down

echo Ambiente parado.
pause
