import json
from pathlib import Path
from app.services.abstract_sensor_service import AbstractSensorService

# HealthcheckService
# ------
# Reads a JSON health‑check file and publishes its content via MQTT.
# Config keys (under services.healthcheck):
#   currentHealthcheckPath (str) – path to the JSON file (default "/tmp/current-healthcheck.json").
# MQTT: No publishing implemented yet; can be added by extending onReady()/publishState().
class HealthcheckService(AbstractSensorService):
    def __init__(self, registry):
        super().__init__("healthcheck", registry)
        self.installed = True

    def onReady(self):
        self.currentHealthcheckPath = Path( self.getServiceConfig().get("currentHealthcheckPath", "/tmp/current-healthcheck.json") )
        super().onReady()

    def readState(self):
        """Liest den aktuellen Healthcheck-Status aus der Datei"""
        if self.currentHealthcheckPath.exists():
            self.getLoggingService().debug(self.name, f" reading {self.currentHealthcheckPath}")
            self.logger.info(self.name, f" reading {self.currentHealthcheckPath}")
            try:
                if self.currentHealthcheckPath.exists():
                    with open(self.currentHealthcheckPath, "r") as f:
                        return json.load(f)
                else:
                    return {"status": "unknown", "error": f"Healthcheck '{self.currentHealthcheckPath}' file not found"}
            except json.JSONDecodeError:
                return {"status": "error", "error": "Invalid JSON format in healthcheck file"}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        else:
            return {"status": "error", "error": f"Could not find '{self.currentHealthcheckPath}' file"}

    def hasSignificantChange(self, oldState, newState):
        return False
