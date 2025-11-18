import subprocess
import json
import threading
import time
import requests
import paho.mqtt.client as mqtt

from app.services.abstract_sensor_service import AbstractSensorService

class UpdateService(AbstractSensorService):
    def __init__(self):
        super().__init__("update")
        self.repoUrl = self.getServiceConfig().get("repoUrl", "https://www.manhart.space/dl/raspi-controller")

    def readState(self):
        """Prüft System- und Script-Updates"""
        return {
            "updates": {
                "system": self._checkSystemUpdates(),
                "script": self._checkScriptUpdates()
            }
        }

    def _checkSystemUpdates(self) -> dict:
        """apt-get Upgrade prüfen"""
        try:
            output = subprocess.check_output(
                ["apt", "-s", "upgrade"], stderr=subprocess.STDOUT
            ).decode("utf-8")

            updates = []
            for line in output.splitlines():
                if line.startswith("Inst "):
                    parts = line.split()
                    pkg = parts[1]
                    version = parts[2].strip("[]")
                    updates.append({"package": pkg, "version": version})

            return {"available": len(updates), "packages": updates}
        except Exception as e:
            return {"error": str(e)}

    def _checkScriptUpdates(self) -> dict:
        """Hier prüfst du dein Git-Repo oder einen Download-Endpunkt"""
        try:
            response = requests.get(f"{self.repoUrl}/VERSION", timeout=5)
            if response.status_code == 200:
                remote_version = response.text.strip()
                with open("VERSION", "r") as f:
                    local_version = f.read().strip()
                return {
                    "local": local_version,
                    "remote": remote_version,
                    "update_available": remote_version != local_version
                }
            return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
