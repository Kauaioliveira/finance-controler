#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/frontend"

if ! command -v npm >/dev/null 2>&1; then
  echo "npm nao encontrado. Instale Node.js antes de continuar."
  exit 1
fi

if [ ! -d "node_modules" ]; then
  echo "Dependencias do frontend ainda nao instaladas."
  echo "Rode: cd frontend && npm install"
  exit 1
fi

if command -v open >/dev/null 2>&1; then
  (sleep 3 && open "http://127.0.0.1:5173") >/dev/null 2>&1 &
fi

exec npm run dev
