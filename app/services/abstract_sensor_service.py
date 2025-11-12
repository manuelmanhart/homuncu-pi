import threading
from datetime import datetime
import time
import json
import paho.mqtt.client as mqtt
from abc import abstractmethod
from app.services.abstract_base_service import AbstractBaseService

class AbstractSensorService(AbstractBaseService):
    def __init__(self, name):
        super().__init__(name)
        self.pollInterval = self.config.get("pollInterval", 30)
        self.publishInterval = self.config.get("publishInterval", 60 * 15)
        self.running = False
        self.client = None
        self.state = None
        self.publishedState = None
        self.lastPublishTime = None
        # Hintergrundthread starten
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        print(f"active: {self.active}")
        if (self.active):
            self.activate()

    def readState(self):
        if self.state == None:
            return self.readNewState()
        else:
            return self.state

    def _poll_loop(self):
        while self.running:
            # we need to start with waiting so the neccessary initializations can be made (since the subclasses call super first)
            time.sleep(self.pollInterval)
            try:
                newState = self.readNewState()
                print(f"publishedState: {self.publishedState} -> newState: {newState}")
                if self.state == None or self.hasSignificantChange(self.publishedState, newState) or self.publishIntervalExceeded():
                    self.publishState(newState)
                self.state = newState
            except Exception as e:
                print(f"[{self.name}] Fehler im Poll-Loop: {e}")

    def publishIntervalExceeded(self) -> bool:
        now = time.time()
        print(f"now: {now} - last publish time: {self.lastPublishTime} > publish interval: {self.publishInterval} => {now - self.lastPublishTime > self.publishInterval}")
        return now - self.lastPublishTime > self.publishInterval

    def hasSignificantChange(self, oldState, newState) -> bool:
        return False

    def publishState(self, state):
        readDateTime = datetime.now().isoformat()
        payload = json.dumps({
            "state": state,
            "timestamp": readDateTime
        })
        self.lastPublishTime = time.time()
        self.publishedState = state
        self.client.publish(self.mqttTopic, payload)
        print(f"[{self.name}] MQTT-Update an {self.mqttTopic}: {payload}")

    @abstractmethod
    def readNewState(self):
        """Implement me in subclasses"""
        raise NotImplementedError

    def activate(self) -> bool:
        if not self.active or not self.running:
            initMqttClient()
            self.running = True
            self.thread.start()
            self.state = self.readNewState()
        self.active = True
        return True

    def initMqttClient(self):
        mqttConfig = self.getGlobalConfig("mqtt")
        self.mqttBaseTopic = mqttConfig.get("baseTopic", "home/raspi")
        mqtt_postfix = name
        self.mqttTopic = f"{self.mqttBaseTopic}/{mqtt_postfix}"
        self.client = mqtt.Client()
        self.client.connect(
            mqttConfig.get("host", "192.168.1.5"),
            mqttConfig.get("port", 1883)
        )

    def deactivate(self) -> bool:
        if self.active:
            self.thread.stop()
        self.active = False
        return True

    def configure(self, config: dict) -> bool:
        return True
