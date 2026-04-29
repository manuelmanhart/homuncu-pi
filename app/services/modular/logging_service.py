from app.services.abstract_sensor_service import AbstractModularBaseService

# LoggingService
# ------
# Reads its own configuration via ConfigService and forwards it to the StdoutLoggingService.
# Config keys (under services.logging): any keys accepted by StdoutLoggingService (e.g. per‑class log levels).
# MQTT: No MQTT interaction – purely internal logging.
class LoggingService(AbstractModularBaseService):
    def __init__(self, registry):
        super().__init__("logging", registry)

    def readState(self):
        config = self.getServiceConfig()
        self.getLoggingService().debug(self.name, self.getServiceConfig())
        self.getLoggingService().setConfig(config)
        return config

    # -----------------------
    # MQTT HANDLER
    # -----------------------
#    def _onMqttMessage(self, topic, payload: dict):
#        self.getLoggingService().debug(self.name, f"Received MQTT: {payload}")
#
#        requestedState = payload.get("state")
#        if requestedState not in ["on", "off"]:
#            self.getLoggingService().error(self.name, f"Invalid state: {requestedState}")
#            return
