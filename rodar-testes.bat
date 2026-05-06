@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Ambiente virtual nao encontrado em .venv\Scripts\python.exe
    echo Rode a instalacao inicial do projeto antes de executar os testes.
    pause
    exit /b 1
)

echo Rodando bateria inicial de testes do backend...
".venv\Scripts\python.exe" -m pytest backend\tests --cov=backend\app --cov-report=term-missing
set EXIT_CODE=%ERRORLEVEL%

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [ERRO] Algum teste falhou.
    pause
    exit /b %EXIT_CODE%
)

echo.
echo [OK] Testes concluidos com sucesso.
pause
