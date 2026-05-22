import os
import shutil
import subprocess
import tarfile
import tempfile

import requests

from app.services.abstract_sensor_service import AbstractSensorService

class UpdateService(AbstractSensorService):
    def __init__(self, registry):
        super().__init__("update", registry)

    def onReady(self):
        config = self.getServiceConfig()
        self.repoUrl = config.get("repoUrl", "https://homuncu.manhart.space/dl")
        self.updateType = config.get("type", "stable")
        self.autoupdate = config.get("autoupdate", "Off")

        self.pollInterval = config.get("pollInterval", 21600)
        self.publishInterval = config.get("publishInterval", 86400)
        self.cacheTTL = 3600

        super().onReady()

    def readState(self):
        system = self._checkSystemUpdates()
        homuncu = self._checkHomuncuUpdates()

        if self.autoupdate in ("System", "All") and system.get("available", 0) > 0:
            self.getLoggingService().info(self.name, "autoupdate: applying system updates")
            self._applySystemUpdates()
            system = self._checkSystemUpdates()
            system["autoupdated"] = True

        if self.autoupdate in ("Homuncu", "All") and homuncu.get("update_available", False):
            self.getLoggingService().info(self.name, "autoupdate: applying homuncu-pi update")
            self._applyHomuncuUpdate(homuncu.get("remote"))
            homuncu = self._checkHomuncuUpdates()
            homuncu["autoupdated"] = True

        return {"system": system, "homuncu": homuncu}

    def _checkSystemUpdates(self) -> dict:
        try:
            self.getLoggingService().info(self.name, "checking system updates")
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

    def _applySystemUpdates(self):
        try:
            subprocess.run(["apt", "upgrade", "-y"], check=False)
            self.getLoggingService().info(self.name, "system updates applied")
        except Exception as e:
            self.getLoggingService().error(self.name, f"system update failed: {e}")

    def _checkHomuncuUpdates(self) -> dict:
        channel = self.updateType
        self.getLoggingService().info(self.name, f"checking homuncu-pi updates ({channel} channel)")
        try:
            version_url = f"{self.repoUrl}/{channel}/VERSION"
            response = requests.get(version_url, timeout=5)
            if response.status_code == 200:
                remote_version = response.text.strip()
                with open("VERSION", "r") as f:
                    local_version = f.read().strip()
                return {
                    "local": local_version,
                    "remote": remote_version,
                    "channel": channel,
                    "update_available": remote_version != local_version,
                }
            return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def _applyHomuncuUpdate(self, remote_version):
        channel = self.updateType
        try:
            archive_name = f"homuncu-pi-{remote_version}.tar.gz"
            archive_url = f"{self.repoUrl}/{channel}/{archive_name}"
            self.getLoggingService().info(self.name, f"downloading {archive_url}")
            resp = requests.get(archive_url, timeout=120)
            if resp.status_code != 200:
                self.getLoggingService().error(self.name, f"download failed: HTTP {resp.status_code}")
                return

            project_root = os.getcwd()
            with tempfile.TemporaryDirectory() as tmp:
                archive_path = os.path.join(tmp, archive_name)
                with open(archive_path, "wb") as f:
                    f.write(resp.content)
                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(path=tmp)
                for item in os.listdir(tmp):
                    if item == archive_name or item in ("config.yaml", "venv"):
                        continue
                    src = os.path.join(tmp, item)
                    dst = os.path.join(project_root, item)
                    if os.path.exists(dst):
                        if os.path.isdir(dst):
                            shutil.rmtree(dst)
                        else:
                            os.remove(dst)
                    shutil.move(src, dst)

            self.getLoggingService().info(self.name, "homuncu-pi update applied, restart recommended")
        except Exception as e:
            self.getLoggingService().error(self.name, f"update failed: {e}")

    def onMqttMessage(self, message):
        self.getLoggingService().info(self.name, f"got message {message}")
        config = self.getServiceConfig()

        if not message.get("repo"):
            self.getLoggingService().warn(
                self.name,
                'Please add a repository name in your message like: {"repo": "myRepository1"}',
            )
        else:
            for r in config.get("repos", []):
                if message.get("repo") == r.get("name"):
                    self.getLoggingService().info(
                        self.name, f'updating repository {r.get("name")} now'
                    )
                    workdir = r.get("path")
                    result = subprocess.run(
                        ["git", "pull"],
                        cwd=workdir,
                        capture_output=True,
                        text=True,
                    )
                    self.getLoggingService().info(f"result: {result}")
                    return
