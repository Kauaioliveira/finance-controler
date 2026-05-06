#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo
echo "===== Validacao do Ambiente (macOS/Linux) ====="
echo

if command -v docker >/dev/null 2>&1; then
  echo "[OK] Docker encontrado."
else
  echo "[ERRO] Docker nao encontrado no PATH."
  exit 1
fi

if docker version >/dev/null 2>&1; then
  echo "[OK] Daemon do Docker acessivel."
else
  echo "[ERRO] Docker Desktop instalado, mas daemon indisponivel."
  echo "       Abra o Docker Desktop e espere a inicializacao completar."
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  echo "[OK] Docker Compose funcionando."
else
  echo "[ERRO] Docker Compose nao respondeu como esperado."
  exit 1
fi

if [ -x ".venv/bin/python" ]; then
  echo "[OK] Ambiente virtual encontrado."
else
  echo "[ERRO] Ambiente virtual nao encontrado."
  exit 1
fi

if command -v npm >/dev/null 2>&1; then
  echo "[OK] Node.js/npm encontrados."
else
  echo "[AVISO] Node.js/npm nao encontrados. O frontend React nao podera subir ainda."
fi

echo
echo "URL esperada da API: http://127.0.0.1:8010/docs"
echo "URL esperada do frontend: http://127.0.0.1:5173"
echo
