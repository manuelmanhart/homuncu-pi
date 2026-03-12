from app.services.abstract_configurable_service import AbstractConfigurableService
from app.services.base.mqtt_service import MqttService
from app.services.service_registry import ServiceRegistry

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