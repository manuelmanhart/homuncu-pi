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

# Ensure system GPIO library (lgpio) is available (check with system Python)
if ! python3 -c "import lgpio" 2>/dev/null; then
    echo "[INFO] Installing system package python3-lgpio..."
    sudo apt install -y python3-lgpio
fi

# Create virtual environment (venv) if not exists
if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] Creating virtual python environment..."
    python3 -m venv --system-site-packages "$VENV_DIR"
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
echo "[INFO] Starting Homuncu PI v${VERSION}..."
python3 -m app.main
