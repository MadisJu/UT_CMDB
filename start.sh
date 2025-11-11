#!/usr/bin/env bash
set -euo pipefail

VENV_DIR=".venv"

if [ "${1:-}" = "--venv" ]; then
  if [ -z "${2:-}" ]; then
    echo "Usage: $0 [--venv PATH] [-- args]" >&2
    exit 2
  fi
  VENV_DIR="$2"
  shift 2
fi

if [ "${1:-}" = "--" ]; then
  shift
fi

if [ ! -d "$VENV_DIR" ]; then
  echo "Virtualenv not found at: $VENV_DIR" >&2
  echo "Create one with: python3 -m venv $VENV_DIR" >&2
  exit 1
fi

# activate venv
# shellcheck disable=SC1091
. "$VENV_DIR/bin/activate"

PY="$VENV_DIR/bin/python"
SCRIPT="src/main.py"

if [ ! -x "$PY" ]; then
  echo "Python executable not found in $VENV_DIR/bin" >&2
  exit 1
fi

if [ ! -f "$SCRIPT" ]; then
  echo "Entry script not found: $SCRIPT" >&2
  exit 1
fi

exec "$PY" "$SCRIPT" "$@"