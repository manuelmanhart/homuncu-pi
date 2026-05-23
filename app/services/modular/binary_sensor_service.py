import pigpio
from app.services.abstract_sensor_service import AbstractSensorService

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

        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise Exception("Could not connect to pigpiod")

        for s in config.get("sensors", []):
            pin = int(s.get("gpioPin"))
            name = s.get("id")
            pull = pigpio.PUD_UP if s.get("pullDirection", "up") == "up" else pigpio.PUD_DOWN
            sensor = {
                "id": name,
                "pin": pin,
                "pull": pull,
                "labelHigh": s.get("labelHigh", "High"),
                "labelLow": s.get("labelLow", "Low"),
                "mqttTopic": s.get("mqttTopic", f"{self.name}/{name}"),
                "lastState": None
            }
            self.pi.set_mode(pin, pigpio.INPUT)
            self.pi.set_pull_up_down(pin, pull)
            self.sensors.append(sensor)
            self.mqttTopic = None
        super().onReady()

    def handleShutdownService(self):
        self.pi.stop()

    def readState(self):
        """
        Returns the state of ALL sensors as dict.
        """
        sensorStates = {}
        if self.sensors:
            for sensor in self.sensors:
                pinState = self.pi.read(sensor["pin"])
                sensorStates[sensor["id"]] = pinState

        return sensorStates

    def publishState(self, state):
        """
        Publishes each sensor independently based on change detection and updates the publishedState at the end.
        """

        publishNeccessary = True #self.state = None or self.publishIntervalExceeded()
        for sensor in self.sensors:
            singleSensorState = state[sensor["id"]]

            # skip if no change and publish time not exceeded yet
            if not publishNeccessary and sensor["lastState"] == singleSensorState:
                continue

            publishState = {
                "number": singleSensorState,
                "label": sensor["labelLow"] if singleSensorState == 0 else sensor["labelHigh"]
            }

            # Publish via parent logic
            self.mqttTopic = sensor["mqttTopic"]
            super().publishState(publishState)
            sensor["lastState"] = singleSensorState

        self.publishedState = state

    def getMqttTopic(self):
        return self.mqttTopic