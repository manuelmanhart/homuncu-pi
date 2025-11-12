import json
import os

from pathlib import Path
from app.env_var_resolver import resolveVariable
from app.services.abstract_sensor_service import AbstractSensorService

class HealthcheckService(AbstractSensorService):
    def __init__(self):
        self.installed = True
        self.currentHealthcheckPath = Path(resolveVariable("/home/${USER}/.config/mmit/healthcheck/${HOSTNAME}/current.json"))
        super().__init__("healthcheck")

    def readNewState(self):
        """Liest den aktuellen Healthcheck-Status aus der Datei"""
        if self.currentHealthcheckPath.exists():
            print(f"[{self.name}] reading {self.currentHealthcheckPath}")
            self.logger.info(f"[{self.name}] reading {self.currentHealthcheckPath}")
            try:
                if self.currentHealthcheckPath.exists():
                    with open(self.currentHealthcheckPath, "r") as f:
                        return json.load(f)
                else:
                    return {"status": "unknown", "error": "Healthcheck '" + self.currentHealthcheckPath + "' file not found"}
            except json.JSONDecodeError:
                return {"status": "error", "error": "Invalid JSON format in healthcheck file"}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
                return {"status": "error", "error": "Could not find '" + self.currentHealthcheckPath + "' file"}
