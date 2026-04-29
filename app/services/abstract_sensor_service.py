from abc import abstractmethod
import threading
import time
import json

from app.services.abstract_modular_base_service import AbstractModularBaseService
from app.services.base.mqtt_service import MqttService
from app.services.base.mqtt_send_flags import MqttSendFlags
from app.services.service_registry import ServiceRegistry

# AbstractSensorService
# ---------------------------------
# Extends AbstractModularBaseService to implement periodic polling sensors and MQTT publishing.
# Config keys (per‑service):
#   pollInterval (int) – seconds between sensor reads.
#   publishInterval (int) – seconds between forced MQTT publishes.
#   mqttTopic (str) – MQTT topic prefix (default is the service name).
#   mqttFlags (str) – pipe‑separated list of MqttSendFlags (e.g. "ADD_BASE_TOPIC,ADD_HOSTNAME,ADD_TIMESTAMP").
# MQTT: Uses getMqttService().sendMessage() with configured flags; receives messages via onMqttMessage().
class AbstractSensorService(AbstractModularBaseService):
    def __init__(self, name, registry, pollInterval = 15, publishInterval = 60 * 15):
        super().__init__(name, registry)
        self.pollInterval = pollInterval
        self.publishInterval = publishInterval

    def onReady(self):
        self.pollInterval = self.getServiceConfig().get("pollInterval", self.pollInterval)
        self.publishInterval = self.getServiceConfig().get("publishInterval", self.publishInterval)
        self.mqttTopic = self.getServiceConfig().get("mqttTopic", None)
        mqttFlagsInConfig = self.getServiceConfig().get("mqttFlags", None)
        if (mqttFlagsInConfig != None):
            self.mqttFlags = MqttSendFlags.parse(mqttFlagsInConfig)
        else:
            self.mqttFlags = MqttSendFlags.ADD_BASE_TOPIC | MqttSendFlags.ADD_HOSTNAME | MqttSendFlags.ADD_TIMESTAMP
        self.running = False
        self.publishedState = None
        self.lastPublishTime = None
        # Hintergrundthread starten
        self.thread = threading.Thread(target=self.pollSensorInThread, daemon=True)
        self.getLoggingService().debug(self.name, f"active: {self.active}")
        if (self.active):
            self.activate()
        super().onReady()

    def getState(self):
        if (not self.active):
            return "Service is not active"
        else:
            state = super().getState()
            self.publishNewStateIfNeccessary(state)
            return state

    def pollSensorInThread(self):
        while self.running:
            # we need to start with waiting so the neccessary initializations can be made (since the subclasses call super first)
            time.sleep(self.pollInterval)
            try:
                self.state = self.getState()
            except Exception as e:
                self.getLoggingService().error(self.name, f"getState failed: {e}")

    def publishNewStateIfNeccessary(self, newState):
        try:
            self.getLoggingService().debug(self.name, f"publishedState: {self.publishedState} -> newState: {newState}")
            if newState != None and (self.publishedState == None or self.hasSignificantChange(self.publishedState, newState) or self.publishIntervalExceeded()):
                self.getLoggingService().debug(self.name, f"publishing newState: {newState}")
                self.publishState(newState)
        except Exception as e:
            self.getLoggingService().debug(self.name, f"Fehler im Poll-Loop: {e}")

    def publishIntervalExceeded(self) -> bool:
        if (self.publishInterval > 0):
            now = time.time()
            timeDiff = abs(now - self.lastPublishTime)
            self.getLoggingService().debug(self.name, f"now: {now} - lastPublishTime: {self.lastPublishTime} => {timeDiff} / {self.publishInterval} => {timeDiff > self.publishInterval}")
            return timeDiff > self.publishInterval
        else:
            return False

    def hasSignificantChange(self, oldState, newState) -> bool:
        return oldState != newState

    def publishState(self, state):
        flags = self.getMqttFlags()
        topic = self.getMqttTopic()
        if (self.mqttTopic != None):
            topic = self.mqttTopic
        # This is not a nice workaround, as 
        # TODO move the wrapping of the message to a static method instead of mqtt service
        if MqttSendFlags.ADD_TIMESTAMP in flags:
            message = state
        else:
            message = json.dumps(state)
        self.getMqttService().sendMessage(topic, message, flags)
        self.lastPublishTime = time.time()
        self.publishedState = state

    def getMqttTopic(self):
        return self.name

    def getMqttFlags(self):
        return self.mqttFlags

    def activate(self) -> bool:
        if not self.active or not self.running:
            self.running = True
            self.thread.start()
        self.active = True
        return True

    def deactivate(self) -> bool:
        if self.active:
            self.thread.stop()
        self.active = False
        return True
