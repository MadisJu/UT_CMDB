#!/usr/bin/env bash
set -euo pipefail

# Build an offline wheelhouse for requirements.txt using an isolated venv
# Run this on a machine with internet AND the same OS/arch + Python minor version
# Usage: ./build.sh

BUILD_VENV=".build-venv"
WHEEL_DIR="wheelhouse"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found in PATH" >&2
  exit 1
fi


rm -rf "$BUILD_VENV"
python3 -m venv "$BUILD_VENV"

. "$BUILD_VENV/bin/activate"

python -m pip install --upgrade pip setuptools wheel


rm -rf "$WHEEL_DIR"
mkdir -p "$WHEEL_DIR"

# Build wheels for all requirements
pip wheel -r requirements.txt -w "$WHEEL_DIR"


cp requirements.txt "$WHEEL_DIR/"
cat > "$WHEEL_DIR/README.txt" <<'EOF'
This folder contains wheels for offline installation.

Copy wheelhouse into the project and run:
  ./scripts/install_offline.sh ./wheelhouse

Notes:
- Build wheels on the same OS/CPU architecture and Python minor version as the offline host.
- Some packages may require system libraries; provide those to the client as needed.
EOF


deactivate || true
rm -rf "$BUILD_VENV"

echo "wheelhouse created: ./$WHEEL_DIR"