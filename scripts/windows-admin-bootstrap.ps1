$ErrorActionPreference = "Stop"

$dockerInstallerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
$dockerInstallerPath = Join-Path $env:TEMP "DockerDesktopInstaller.exe"

Write-Host "Habilitando WSL e VirtualMachinePlatform..."
dism.exe /online /Enable-Feature /FeatureName:Microsoft-Windows-Subsystem-Linux /All /NoRestart
dism.exe /online /Enable-Feature /FeatureName:VirtualMachinePlatform /All /NoRestart

Write-Host "Instalando WSL..."
wsl.exe --install --no-distribution

Write-Host "Baixando Docker Desktop..."
Invoke-WebRequest -Uri $dockerInstallerUrl -OutFile $dockerInstallerPath

Write-Host "Instalando Docker Desktop com backend WSL 2..."
Start-Process -FilePath $dockerInstallerPath -Wait -ArgumentList "install", "--accept-license", "--backend=wsl-2"

Write-Host ""
Write-Host "Bootstrap concluido. Reinicie o Windows antes de abrir o Docker Desktop." -ForegroundColor Yellow
