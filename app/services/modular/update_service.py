import subprocess
import requests

from app.services.abstract_sensor_service import AbstractSensorService

class UpdateService(AbstractSensorService):
    def __init__(self, registry):
        super().__init__("update", registry)

    def onReady(self):
        self.repoUrl = self.getServiceConfig().get("repoUrl", "https://www.manhart.space/dl/raspi-controller")
        super().onReady()

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

    def onMqttMessage(self, message):
        currentState = self.readState()
        self.getLoggingService().info(self.name, f"got message {message}")
        config = self.getServiceConfig()

        self.getLoggingService().debug(self.name, f" serviceConfig: {config}")

        if not message.get("repo"):
            self.getLoggingService().warn(self.name, "Please add a repository name in your message like: {\"repo\": \"myRepository1\"}")
        else:
            for r in config.get("repos", []):
                if message.get("repo") == r.get("name"):
                    self.getLoggingService().info(self.name, f"updating repository {r.get("name")} now")
                    workdir = r.get("path")
                    result = subprocess.run(
                        ["git", "pull"],
                        cwd=workdir,
                        capture_output=True,
                        text=True
                    )
                    self.getLoggingService().info(f"result: {result}")
                    return
