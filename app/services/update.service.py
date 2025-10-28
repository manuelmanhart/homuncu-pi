from datetime import datetime
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

    def initStatus(self) -> bool:
        # initialer Status
        self.installed = True
        self.active = True # TBD should be read from a file on startup
        #self.state = self.readState()
        return True

    def configure(self, config: dict):
        """Konfiguration aus JSON übernehmen"""
        self.interval = config.get("interval", self.interval)
        self.mqtt_enabled = config.get("mqtt_enabled", self.mqtt_enabled)
        self.mqtt_host = config.get("mqtt_host", self.mqtt_host)
        self.mqtt_topic = config.get("mqtt_topic", self.mqtt_topic)

    def activate(self):
        if not self.active:
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()
        self.state = self.readState()
        return True

    def deactivate(self):
        if self.active:
            self.thread.stop()
        return False

    def readState(self):
        """Prüft System- und Script-Updates"""
        now = datetime.now()

        return {
            "date": now.strftime("%Y-%m-%d"), # 2025-09-19
            "time": now.strftime("%H:%M:%S"), # 18:30:15
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
            repo_url = "https://www.manhart.space/dl/VERSION"
            response = requests.get(repo_url, timeout=5)
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

    def send_mqtt(self, data: dict):
        """Ergebnis an MQTT-Broker senden"""
        try:
            client = mqtt.Client()
            client.connect(self.mqtt_host)
            payload = json.dumps(data)
            client.publish(self.mqtt_topic, payload)
            client.disconnect()
        except Exception as e:
            print(f"[ERROR] MQTT Publish failed: {e}")
