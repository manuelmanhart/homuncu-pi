import json
import os

from pathlib import Path
from app.env_var_resolver import resolveVariable
from app.services.abstract_sensor_service import AbstractSensorService

class HealthcheckService(AbstractSensorService):
    def __init__(self):
        super().__init__("healthcheck")
        self.installed = True
        self.currentHealthcheckPath = Path(resolveVariable("/home/${USER}/.config/mmit/healthcheck/${HOSTNAME}/current.json"))

    def readNewState(self):
        """Liest den aktuellen Healthcheck-Status aus der Datei"""
        print(f"[{self.name}] reading {self.currentHealthcheckPath}")
        self.logger.info(f"[{self.name}] reading {self.currentHealthcheckPath}")
        try:
            if self.currentHealthcheckPath.exists():
                with open(self.currentHealthcheckPath, "r") as f:
                    self.state = json.load(f)
            else:
                self.state = {"status": "unknown", "error": "Healthcheck '" + self.currentHealthcheckPath + "' file not found"}
        except json.JSONDecodeError:
            self.state = {"status": "error", "error": "Invalid JSON format in healthcheck file"}
        except Exception as e:
            self.state = {"status": "error", "error": str(e)}


    def activate(self):
        return self.currentHealthcheckPath.exists()

    def deactivate(self):
        return self.currentHealthcheckPath.exists()
