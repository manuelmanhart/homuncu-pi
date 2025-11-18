#!/bin/bash
set -e

# Define script variables
BASE_DIR="$(cd "$(dirname "$0")"; pwd)"
VENV_DIR="$BASE_DIR/venv"
REQ_FILE_NAME="requirements.txt"
REQ_FILE_PATH="$BASE_DIR/$REQ_FILE_NAME"
INSTALL_REQUIREMENTS=0
PORT=8000
VERSION=$(cat $BASE_DIR/VERSION)

if [ "$1" == "-u" ]; then
    INSTALL_REQUIREMENTS=1
fi

# Create virtual environment (venv) if not exists
if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] Creating virtual python environment..."
    python3 -m venv "$VENV_DIR"
    INSTALL_REQUIREMENTS=1
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Install / update dependencies if neccessary
if [ $INSTALL_REQUIREMENTS == 0 ]; then
    echo "[INFO] Per default no Python dependencies are checked (call with -u param to update)"
elif [ -f "$REQ_FILE_PATH" ]; then
    echo "[INFO] Installing / updating dependencies (can take a while)..."
    pip install --upgrade pip >/dev/null
    pip install  --prefer-binary -r "$REQ_FILE_PATH" -v
else
    echo "[WARN] No $REQ_FILE_NAME found!"
fi

# Starting python script
echo "[INFO] Starting RasPi Controller v${VERSION}..."
# TODO start service without uvicorn
python3 -m app.main
