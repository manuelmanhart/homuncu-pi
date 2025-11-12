from app.services.abstract_base_service import AbstractBaseService
import subprocess

class CameraService(AbstractBaseService):
    def __init__(self):
        super().__init__("camera")

    def readState(self):
        return False

    def activate(self) -> bool:
        result = subprocess.run(
            ["systemctl", "is-active", "squeezelite"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0 and result.stdout.strip() == "active"

    def deactivate(self) -> bool:
        self.active = False
        return True

    def configure(self, config: dict) -> bool:
        self.config.update(config)
        return True
