import threading
from datetime import datetime
import time
import json
from abc import abstractmethod
from app.services.abstract_modular_base_service import AbstractModularBaseService
from app.services.base.mqtt_service import MqttService
from app.services.di_helper import getService

class AbstractSensorService(AbstractModularBaseService):
    def __init__(self, name, pollInterval = 15, publishInterval = 60 * 15):
        super().__init__(name)
        self.pollInterval = self.getServiceConfig().get("pollInterval", pollInterval)
        self.publishInterval = self.getServiceConfig().get("publishInterval", publishInterval)
        self.appendHostnameToTopic = self.getServiceConfig().get("appendHostnameToTopic", False)
        self.running = False
        self.publishedState = None
        self.lastPublishTime = None
        # Hintergrundthread starten
        self.thread = threading.Thread(target=self.pollSensorInThread, daemon=True)
        self.getLoggingService().debug(self.name, f"active: {self.active}")
        if (self.active):
            self.activate()

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
                self.publishState(self.name, newState)
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

    def publishState(self, mqttTopic: str, state):
        readDateTime = datetime.now().isoformat()
        payload = json.dumps({
            "state": state,
            "timestamp": readDateTime
        })
        self.lastPublishTime = time.time()
        self.publishedState = state
        self.getMqttService().sendMessage(self.name, payload, self.appendHostnameToTopic)

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
