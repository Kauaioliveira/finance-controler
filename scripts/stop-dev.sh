#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker nao encontrado no PATH."
  exit 1
fi

if ! docker version >/dev/null 2>&1; then
  echo "O daemon do Docker nao esta acessivel."
  echo "Abra o Docker Desktop antes de usar este script."
  exit 1
fi

echo "Derrubando containers do projeto..."
docker compose down
echo "Ambiente parado."
