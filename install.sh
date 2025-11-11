#!/usr/bin/env bash
set -euo pipefail

WH_DIR="${1:-}"
if [ -z "$WH_DIR" ] || [ ! -d "$WH_DIR" ]; then
  echo "Usage: $0 /path/to/wheelhouse"
  exit 2
fi

python3 -m venv .venv
. .venv/bin/activate

python -m pip install --upgrade pip
pip install --no-index --find-links "$WH_DIR" -r "$WH_DIR/requirements.txt"

echo "Offline install complete. Activate with: source .venv/bin/activate"