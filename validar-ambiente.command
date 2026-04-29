#!/bin/bash
cd "$(dirname "$0")"
./scripts/validate-env.sh
echo
read -n 1 -s -r -p "Pressione qualquer tecla para continuar..."
