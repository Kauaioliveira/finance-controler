@echo off
setlocal

cd /d "%~dp0"

echo.
echo ===== Validacao do Ambiente =====
echo.

where docker >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Docker nao encontrado no PATH.
    goto end
) else (
    echo [OK] Docker encontrado.
)

docker version >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Docker Desktop instalado, mas daemon indisponivel.
    echo        Abra o Docker Desktop e espere a inicializacao completar.
    goto check_python
) else (
    echo [OK] Daemon do Docker acessivel.
)

docker compose ps >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Docker Compose nao respondeu como esperado.
) else (
    echo [OK] Docker Compose funcionando.
)

:check_python
if exist ".venv\Scripts\python.exe" (
    echo [OK] Ambiente virtual encontrado.
) else (
    echo [ERRO] Ambiente virtual nao encontrado.
)

where npm.cmd >nul 2>nul
if errorlevel 1 (
    echo [AVISO] Node.js/npm nao encontrados. O frontend React nao podera subir ainda.
) else (
    echo [OK] Node.js/npm encontrados.
    if exist "frontend\package.json" (
        echo [OK] Frontend React detectado em frontend\package.json
    )
)

echo.
echo URL esperada da API: http://127.0.0.1:8010/docs
echo URL esperada do frontend: http://127.0.0.1:5173
echo.

:end
pause
