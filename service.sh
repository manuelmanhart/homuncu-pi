#!/bin/bash
set -e

# === Konfiguration anpassen ===
SERVICE_NAME="raspi-controller"
WORK_DIR="$(cd "$(dirname "$0")"; pwd)"
#USER="manuel"        # ggf. anpassen (z. B. dein Linux-User)
PORT=8000
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

function install() {
    echo "[INFO] Installiere ${SERVICE_NAME} Service..."

    local status=$(sudo systemctl status ${SERVICE_NAME})
    if [ "$status" != "Unit ${SERVICE_NAME}.service could not be found." ]; then
        # systemd Service-Datei schreiben
        sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Pi Controller for plug and play homeautomation
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
    else
        echo "[INFO] Service ist bereits installiert, restarte..."
        sudo systemctl restart ${SERVICE_NAME}
    fi
    echo "[INFO] Installation abgeschlossen!"
    echo "  Status prüfen:   sudo systemctl status ${SERVICE_NAME}"
    echo "  Logs verfolgen:  journalctl -u ${SERVICE_NAME} -f"
    echo "  API testen:      http://<pi-ip>:${PORT}/status"
}

function help() {
	local progName=$(echo "$0" | rev | cut -d'/' -f1 | rev)

	cat <<-END
	GENERAL: $progName is a helper for manageing the service regarding $SERVICE_NAME.
	
	USAGE:
	    $progName command [arguments]
	    $progName help [topic]
	
	The commands are:
	END

	ls -1 "${HELP_PATH}"

	cat <<-END

	Use "$progName help <command>" for more information about a command.

	END

	if [ ! -z $1 ]; then
		echo "TOPIC: $1"
		echo ""
		cat "${HELP_PATH}/$1"
	fi

	exit
}

function parseArgs() {
	if [ -z "$1" ]; then
		help
	fi
}

function runScript() {
	local isParseArgsDefined=$(type -t parseArgs-$ACTION)
	if [ "function" == "$isParseArgsDefined" ]; then
		"parseArgs-$ACTION" "${@:2}"
	fi
	"$ACTION" "${@:2}"
}
# main script

ACTION=${1:-"help"}

# parse given arguments
parseArgs "$@"

# run script
runScript "$@"
