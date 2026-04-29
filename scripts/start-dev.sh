#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -x ".venv/bin/python" ]; then
  echo "Ambiente virtual nao encontrado em .venv/bin/python"
  echo "Rode scripts/setup-mac.sh antes de continuar."
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker nao encontrado no PATH."
  exit 1
fi

if ! docker version >/dev/null 2>&1; then
  echo "O Docker Desktop parece instalado, mas o daemon nao esta acessivel."
  echo "Abra o Docker Desktop e espere ele terminar de iniciar."
  exit 1
fi

echo "Subindo PostgreSQL com pgvector..."
docker compose up -d postgres

echo "Aguardando banco ficar saudavel..."
for _ in $(seq 1 30); do
  status="$(docker inspect --format '{{.State.Health.Status}}' assistente-contabil-postgres 2>/dev/null || true)"
  if [ "$status" = "healthy" ]; then
    break
  fi
  sleep 2
done

if command -v open >/dev/null 2>&1; then
  (sleep 4 && open "http://127.0.0.1:8010/docs") >/dev/null 2>&1 &
fi

echo "Subindo API em http://127.0.0.1:8010 ..."
exec ".venv/bin/python" -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
