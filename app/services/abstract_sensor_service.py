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
        self.thread = threading.Thread(target=self.pollSensorInThread, daemon=True)
        print(f"active: {self.active}")
        if (self.active):
            self.activate()

    def readState(self):
        if self.state == None:
            return self.readNewStateAndPublishIfNeccessary()
        else:
            return self.state

    def pollSensorInThread(self):
        while self.running:
            # we need to start with waiting so the neccessary initializations can be made (since the subclasses call super first)
            time.sleep(self.pollInterval)
            self.readNewStateAndPublishIfNeccessary()

    def readNewStateAndPublishIfNeccessary(self):
            try:
                newState = self.readNewState()
                print(f"[{self.name}] publishedState: {self.publishedState} -> newState: {newState}")
                if newState != None and (self.publishedState == None or self.hasSignificantChange(self.publishedState, newState) or self.publishIntervalExceeded()):
                    print(f"[{self.name}] publishing newState: {newState}")
                    self.publishState(newState)
                self.state = newState
            except Exception as e:
                print(f"[{self.name}] Fehler im Poll-Loop: {e}")

    def publishIntervalExceeded(self) -> bool:
        now = time.time()
        print(f"[DEBUG] [{self.name}] now: {now} - last publish time: {self.lastPublishTime} > publish interval: {self.publishInterval} => {now - self.lastPublishTime > self.publishInterval}")
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
        if (self.client != None):
            self.client.publish(self.mqttTopic, payload)
            print(f"[{self.name}] Sending MQTT message to {self.mqttTopic} with payload {payload}")
        else:
            print(f"[{self.name}] Cannot send MQTT message, check your mqtt config")

    @abstractmethod
    def readNewState(self):
        """Implement me in subclasses"""
        raise NotImplementedError

    def activate(self) -> bool:
        if not self.active or not self.running:
            self.initMqttClient()
            self.running = True
            self.thread.start()
            self.state = self.readNewState()
        self.active = True
        return True

    def initMqttClient(self):
        mqttConfig = self.getGlobalConfig("mqtt")
        mqttHost = mqttConfig.get("host", "")
        mqttPort = mqttConfig.get("port", "")
        mqttBaseTopic = mqttConfig.get("baseTopic", "")
        print(f"[DEBUG] [{self.name}] mqttConfig: {mqttHost}:{mqttPort}/{mqttBaseTopic}")
        if (mqttBaseTopic != "" and mqttHost != "" and mqttPort != ""):
            self.mqttTopic = f"{mqttBaseTopic}/{self.name}"
            self.client = mqtt.Client()
            self.client.connect(
                mqttHost,
                mqttPort
            )
        else:
            self.client = None

    def deactivate(self) -> bool:
        if self.active:
            self.thread.stop()
        self.active = False
        return True

    def configure(self, config: dict) -> bool:
        return True
