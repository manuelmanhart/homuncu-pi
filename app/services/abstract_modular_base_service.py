from app.services.abstract_configurable_service import AbstractConfigurableService
from app.services.base.mqtt_service import MqttService
from app.services.service_registry import ServiceRegistry

# AbstractModularBaseService
# ---------------------------------
# Base for services that are loaded dynamically (modular). Handles activation flag and MQTT integration.
# Config keys (per‑service):
#   active: bool – whether the service should be started.
#   mqttTopic / mqttFlags – optional MQTT publishing settings (used by AbstractSensorService).
# MQTT: Provides getMqttService() to send messages, and onMqttMessage() hook for incoming messages.
class AbstractModularBaseService(AbstractConfigurableService):
    """
    Abstract base class for all modular services
    """
    def __init__(self, name: str, registry):
        super().__init__(name, registry)

    def onReady(self):
        self.active = self.getServiceConfig().get("active", self.active)
        self.getLoggingService().debug(self.name, f"service config {self.getServiceConfig()} -> active {self.active}")
        super().onReady()

    def onMqttMessage(self, message):
        # TBD the mqtt service should send an internal event / message
        return

#    def publishStateToMqtt(self):
#        getMqttService().sendMessage()

    def getState(self) -> dict:
        if (not self.active):
            return "Service is not active"
        else:
            return super().getState()

    def getMqttService(self):
        return self.getService(MqttService)