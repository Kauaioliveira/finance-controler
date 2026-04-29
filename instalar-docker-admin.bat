@echo off
setlocal

cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process PowerShell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File ""%cd%\scripts\windows-admin-bootstrap.ps1""'"

echo O PowerShell de administrador foi aberto.
echo Aceite o UAC e aguarde a instalacao terminar.
pause
