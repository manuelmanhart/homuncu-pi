#!/bin/bash
set -e

# === Konfiguration anpassen ===
SERVICE_NAME="raspi-controller"
WORK_DIR="$(cd "$(dirname "$0")"; pwd)"
USER="pi"        # ggf. anpassen (z. B. dein Linux-User)
PORT=8000

SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "[INFO] Installiere ${SERVICE_NAME} Service..."

# systemd Service-Datei schreiben
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Pi Control API
After=network.target

[Service]
Type=simple
WorkingDirectory=${WORK_DIR}
ExecStart=${WORK_DIR}/run.sh
Restart=always
User=${USER}
Environment="PATH=${WORK_DIR}/venv/bin:/usr/bin:/bin"

[Install]
WantedBy=multi-user.target
EOF

# systemd neu laden
echo "[INFO] Lade systemd neu..."
sudo systemctl daemon-reload

# Service aktivieren und starten
echo "[INFO] Aktiviere und starte Service..."
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl restart ${SERVICE_NAME}

echo "[INFO] Installation abgeschlossen!"
echo "  Status prüfen:   sudo systemctl status ${SERVICE_NAME}"
echo "  Logs verfolgen:  journalctl -u ${SERVICE_NAME} -f"
echo "  API testen:      http://<pi-ip>:${PORT}/status"
