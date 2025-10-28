#!/bin/bash
set -e

# Basis-Verzeichnis des Projekts
BASE_DIR="$(cd "$(dirname "$0")"; pwd)"
VENV_DIR="$BASE_DIR/venv"
REQ_FILE="$BASE_DIR/requirements.txt"
INSTALL_REQUIREMENTS=0

if [ "$1" == "-u" ]; then
    INSTALL_REQUIREMENTS=1
fi

# Virtuelle Umgebung anlegen, falls nicht vorhanden
if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] Erstelle virtuelles Environment..."
    python3 -m venv "$VENV_DIR"
    INSTALL_REQUIREMENTS=1
fi

# Aktivieren
source "$VENV_DIR/bin/activate"

# Abhängigkeiten installieren/aktualisieren falls nötig
if [ $INSTALL_REQUIREMENTS == 0 ]; then
    echo "[INFO] Per default werden keine Python-Abhängigkeiten geprüft"
elif [ -f "$REQ_FILE" ]; then
    echo "[INFO] Prüfe/Installiere Python-Abhängigkeiten..."
    pip install --upgrade pip >/dev/null
    pip install -r "$REQ_FILE" >/dev/null
else
    echo "[WARN] Keine requirements.txt gefunden!"
fi

# Starte FastAPI über uvicorn
VERSION=$(cat $BASE_DIR/VERSION)
echo "[INFO] Starte Pi Control API v${VERSION}..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
