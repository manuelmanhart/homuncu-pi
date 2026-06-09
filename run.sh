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

# Check if squeezelite is needed (based on config), install and configure
if [ -f "$BASE_DIR/config.yaml" ] && grep -q '^  squeezebox:' "$BASE_DIR/config.yaml"; then
    if grep -A1 '^  squeezebox:' "$BASE_DIR/config.yaml" | grep -qi 'active:\s*true'; then
        if ! command -v squeezelite &>/dev/null; then
            echo "[INFO] Installing system package squeezelite..."
            sudo apt install -y squeezelite
        fi
        # Copy template and configure LMS server
        TEMPLATE="$BASE_DIR/templates/squeezelite.conf"
        if [ -f "$TEMPLATE" ]; then
            LMS_SERVER=$(grep -A2 '^  squeezebox:' "$BASE_DIR/config.yaml" | grep 'lmsServer:' | awk -F': ' '{print $2}' | tr -d '"' || true)
            if [ -n "$LMS_SERVER" ]; then
                echo "[INFO] Configuring squeezelite with LMS server $LMS_SERVER..."
                sudo cp "$TEMPLATE" /etc/default/squeezelite
                sudo sed -i "s/__LMS_SERVER__/$LMS_SERVER/g" /etc/default/squeezelite
                if systemctl is-enabled squeezelite &>/dev/null; then
                    sudo systemctl restart squeezelite
                fi
                echo "[INFO] Squeezelite configured"
            fi
        fi
    fi
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
