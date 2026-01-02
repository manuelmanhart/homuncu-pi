#!/bin/bash
set -e

# === Konfiguration anpassen ===
SERVICE_NAME="raspi-controller"
WORK_DIR="$(cd "$(dirname "$0")"; pwd)"
#USER="manuel"        # ggf. anpassen (z. B. dein Linux-User)
PORT=8000
SERVICE_FILE_NAME="${SERVICE_NAME}.service"
SERVICE_FILE_PATH="/etc/systemd/system/${SERVICE_FILE_NAME}"
HELP_PATH=${BASH_SOURCE%/*}/help

function install() {
    echo "[INFO] Installing ${SERVICE_NAME} service..."

    local status=$(sudo systemctl status ${SERVICE_FILE_NAME})
    if [ "$status" != "Unit ${SERVICE_FILE_NAME} could not be found." ]; then
        # systemd Service-Datei schreiben
        sudo tee "$SERVICE_FILE_PATH" > /dev/null <<EOF
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
        echo "[INFO] Reloading system daemon..."
        sudo systemctl daemon-reload

        # Service aktivieren und starten
        echo "[INFO] Activate and start Service ${SERVICE_NAME} ..."
        sudo systemctl enable ${SERVICE_NAME}
        sudo systemctl restart ${SERVICE_NAME}
    else
        echo "[INFO] Service already installed, restarting..."
        sudo systemctl restart ${SERVICE_NAME}
    fi
    echo "[INFO] Installation successful!"
    echo "  Check service state:  sudo systemctl status ${SERVICE_NAME}"
    echo "  Tail logs:            journalctl -u ${SERVICE_NAME} -f"
    echo "                     or ./service.sh status"
    echo "  Call API:             http://<pi-ip>:${PORT}/status"
}

function status() {
    echo "[INFO] Status of ${SERVICE_NAME} service..."
    local options="$*"
    if [ "$options" != "" ]; then
        echo "OPTIONS: $options"
    fi
    local status=$(sudo systemctl status ${SERVICE_FILE_NAME})

    if [ "$status" == "Unit ${SERVICE_FILE_NAME} could not be found." ]; then
        echo "[INFO] Service ${SERVICE_NAME} is not installed."
    else
        local isActive=$(echo $status | grep "Active:")
        if [ "$isActive" != "" ]; then
            echo "[INFO] Service ${SERVICE_NAME} is running"
            echo ""
            journalctl -u ${SERVICE_NAME} ${options} -f
        else
            echo "[INFO] Service ${SERVICE_NAME} not running"
        fi
    fi
}

function uninstall() {
    echo "[INFO] Uninstalling ${SERVICE_NAME} service..."

    local status=$(sudo systemctl status ${SERVICE_NAME})
    if [ "$status" == "Unit ${SERVICE_FILE_NAME} could not be found." ]; then
		echo "Service ${SERVICE_FILE_NAME} is not installed."
	else
        # systemd Service-Datei schreiben
        sudo rm "$SERVICE_FILE_PATH" > /dev/null

        echo "[INFO] Removing service..."
        sudo systemctl disable ${SERVICE_NAME}
        sudo systemctl stop ${SERVICE_NAME}
        # relaod systemd
        echo "[INFO] Reloading system daemon..."
        sudo systemctl daemon-reload
    fi
    echo "[INFO] Uninstallation successful!"
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
