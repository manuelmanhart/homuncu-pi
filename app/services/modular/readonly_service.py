from app.services.abstract_modular_base_service import AbstractModularBaseService
import subprocess

# TODO implement correctly
class ReadOnlyService(AbstractModularBaseService):
    def __init__(self):
        super().__init__("readonly")

    def readState(self) -> bool:
        return False
