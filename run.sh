#!/bin/bash
# Arranca SchematicBuq desde el código fuente (desarrollo).
cd "$(dirname "$0")" || exit 1
exec python3 main.py "$@"
