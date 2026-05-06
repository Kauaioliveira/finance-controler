#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
chmod +x ./scripts/test-backend.sh
./scripts/test-backend.sh
