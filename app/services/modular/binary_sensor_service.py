from app.services.abstract_sensor_service import AbstractSensorService
from gpiozero import DigitalInputDevice

# BinarySensorService
# ------
# Reads multiple GPIO pins as binary sensors and publishes their state via MQTT.
# Config keys (under services.binarySensor):
#   sensors: list of sensor definitions, each with:
#       id (str) – sensor identifier.
#       pin (int) – GPIO pin number.
#       pullDirection (str) – "up" (default) or "down" for pull resistor.
#       labelHigh / labelLow (str) – human readable labels.
#       mqttTopic (str) – optional MQTT topic for this sensor (defaults to "binarySensor/<id>").
# MQTT: Publishes each sensor change using getMqttService().sendMessage() with flags ADD_BASE_TOPIC|ADD_HOSTNAME|ADD_TIMESTAMP.
class BinarySensorService(AbstractSensorService):
    def __init__(self, registry):
        self.sensors = []
        super().__init__("binarySensor", registry)

    def onReady(self):
        # List of sensor definitions
        config = self.getServiceConfig()

        self.getLoggingService().debug(self.name, f" serviceConfig: {config}")

        for s in config.get("sensors", []):
            pin = int(s.get("gpioPin"))
            name = s.get("id")
            pull_up = s.get("pullDirection", "up") == "up"
            device = DigitalInputDevice(pin, pull_up=pull_up)
            sensor = {
                "id": name,
                "device": device,
                "labelHigh": s.get("labelHigh", "High"),
                "labelLow": s.get("labelLow", "Low"),
                "mqttTopic": s.get("mqttTopic", f"{self.name}/{name}"),
                "lastState": None,
            }
            self.sensors.append(sensor)
            self.mqttTopic = None
        super().onReady()

    def handleShutdownService(self):
        for s in self.sensors:
            s["device"].close()

    def readState(self):
        """
        Returns the state of ALL sensors as dict.
        """
        sensorStates = {}
        if self.sensors:
            for s in self.sensors:
                sensorStates[s["id"]] = 1 if s["device"].is_active else 0
        return sensorStates

    def publishState(self, state):
        """
        Publishes each sensor independently based on change detection and updates the publishedState at the end.
        """
        publishNeccessary = True
        for s in self.sensors:
            singleSensorState = state[s["id"]]
            if not publishNeccessary and s["lastState"] == singleSensorState:
                continue
            publishState = {
                "number": singleSensorState,
                "label": s["labelLow"] if singleSensorState == 0 else s["labelHigh"],
            }
            self.mqttTopic = s["mqttTopic"]
            # Publish via parent logic
            super().publishState(publishState)
            s["lastState"] = singleSensorState
        self.publishedState = state

    def getMqttTopic(self):
        return self.mqttTopic
