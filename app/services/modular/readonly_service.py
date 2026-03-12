from app.services.abstract_modular_base_service import AbstractModularBaseService
import subprocess

# TODO implement correctly
class ReadOnlyService(AbstractModularBaseService):
    def __init__(self, registry):
        super().__init__("readonly", registry)

    def readState(self) -> bool:
        return False
