#!/bin/bash
cd "$(dirname "$0")"
./scripts/stop-dev.sh
echo
read -n 1 -s -r -p "Pressione qualquer tecla para continuar..."
