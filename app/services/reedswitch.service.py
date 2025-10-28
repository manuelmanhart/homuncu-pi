from app.services.abstract_sensor_service import AbstractSensorService
import subprocess

class ReedSwitchService(AbstractSensorService):
    def __init__(self):
        super().__init__("reedswitch")

    def initStatus(self) -> bool:
        result = subprocess.run(
            ["systemctl", "is-enabled", "squeezelite"],
            capture_output=True,
            text=True
        )
        self.installed = (result.returncode == 0)
        result = subprocess.run(
            ["systemctl", "is-active", "squeezelite"],
            capture_output=True,
            text=True
        )
        self.active = (result.returncode == 0 and result.stdout.strip() == "active")
        return True

    def readState(self):
        return True

    def install(self) -> bool:
        return True

    def uninstall(self) -> bool:
        return True

    def activate(self) -> bool:
        result = subprocess.run(
            ["systemctl", "start", "squeezelite"],
            capture_output=True,
            text=True
        )
        return (result.returncode == 0)

    def deactivate(self) -> bool:
        result = subprocess.run(
            ["systemctl", "stop", "squeezelite"],
            capture_output=True,
            text=True
        )
        return (result.returncode == 0)

    def configure(self, config: dict) -> bool:
        self.config.update(config)
        return True
