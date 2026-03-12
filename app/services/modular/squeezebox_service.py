from app.services.abstract_modular_base_service import AbstractModularBaseService
import subprocess

class SqueezeboxService(AbstractModularBaseService):
    def __init__(self, registry):
        super().__init__("squeezebox", registry)

    def readState(self) -> bool:
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
        return self.active

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
