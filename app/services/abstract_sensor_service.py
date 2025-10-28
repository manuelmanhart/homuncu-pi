import threading
import time
import json
import paho.mqtt.client as mqtt
from abc import abstractmethod
from app.services.abstract_base_service import AbstractBaseService

class AbstractSensorService(AbstractBaseService):
    def __init__(self, name):
        super().__init__(name)
        cfg = self.getServiceConfig()
        self.pollInterval=cfg.get("pollInterval", 30)
        self.tolerance=cfg.get("temperatureTolerance", 0.5)
        self.current_state = None
        self.running=False

        # MQTT-Konfiguration aus globaler Config
        mqtt_cfg = self.getGlobalConfig("mqtt")
        self.mqtt_base_topic = mqtt_cfg.get("base_topic", "home/raspi")
        mqtt_postfix = name
        self.mqtt_topic = f"{self.mqtt_base_topic}/{mqtt_postfix}"
        self.client = mqtt.Client()
        self.client.connect(
            mqtt_cfg.get("host", "localhost"),
            mqtt_cfg.get("port", 1883)
        )

        # Hintergrundthread starten
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)

    def start(self):
        #super().start()
        self.running=True
        self.thread.start()

    @abstractmethod
    def readState(self):
        """Von Subklassen zu implementieren"""
        raise NotImplementedError

    def _poll_loop(self):
        while self.running:
            try:
                newState = self.readState()
                print(f"state: {self.current_state} -> {newState}")
                if self.hasSignificantChange(newState):
                    self.current_state = newState
                    self.publish_state(newState)
            except Exception as e:
                print(f"[{self.name}] Fehler im Poll-Loop: {e}")
            time.sleep(self.pollInterval)

    def hasSignificantChange(self, newState) -> bool:
        return False

    def publish_state(self, state):
        payload = json.dumps({
            "service": self.name,
            "state": state,
            "timestamp": time.time()
        })
        self.client.publish(self.mqtt_topic, payload)
        print(f"[{self.name}] MQTT-Update an {self.mqtt_topic}: {payload}")

    @abstractmethod
    def activate(self) -> bool:
        return True

    @abstractmethod
    def deactivate(self) -> bool:
        return True

    @abstractmethod
    def configure(self, config: dict) -> bool:
        return True
