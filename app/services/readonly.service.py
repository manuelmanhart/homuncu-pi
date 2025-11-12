from app.services.abstract_base_service import AbstractBaseService
import subprocess

# TODO implement correctly
class ReadOnlyService(AbstractBaseService):
    def __init__(self):
        super().__init__("readonly")

    def readState(self) -> bool:
        return False

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
