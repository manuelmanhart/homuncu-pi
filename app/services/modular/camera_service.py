from app.services.abstract_modular_base_service import AbstractModularBaseService
import subprocess

# TODO implement correctly
class CameraService(AbstractModularBaseService):
    def __init__(self, registry):
        super().__init__("camera", registry)

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
