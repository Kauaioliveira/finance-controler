@echo off
setlocal

cd /d "%~dp0"

if not exist "frontend\package.json" (
    echo Frontend React nao encontrado em frontend\package.json
    pause
    exit /b 1
)

where npm.cmd >nul 2>nul
if errorlevel 1 (
    echo npm.cmd nao encontrado no PATH.
    echo Instale o Node.js antes de usar este atalho.
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo Dependencias do frontend ainda nao instaladas.
    echo Rode: cd frontend ^&^& npm.cmd install
    pause
    exit /b 1
)

echo Abrindo frontend React em http://127.0.0.1:5173 ...
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 4; Start-Process 'http://127.0.0.1:5173'"
cd /d "%~dp0frontend"
npm.cmd run dev
