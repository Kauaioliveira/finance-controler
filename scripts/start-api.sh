#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -x ".venv/bin/python" ]; then
  echo "Ambiente virtual nao encontrado em .venv/bin/python"
  echo "Rode scripts/setup-mac.sh antes de continuar."
  exit 1
fi

if command -v open >/dev/null 2>&1; then
  (sleep 3 && open "http://127.0.0.1:8010/docs") >/dev/null 2>&1 &
fi

echo "Subindo apenas a API em http://127.0.0.1:8010 ..."
exec ".venv/bin/python" -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
