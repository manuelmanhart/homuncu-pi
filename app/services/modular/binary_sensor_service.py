import pigpio
from app.services.abstract_sensor_service import AbstractSensorService

class BinarySensorService(AbstractSensorService):
    def __init__(self):
        self.sensors = []  
        super().__init__("binarySensor")
        # List of sensor definitions
        config = self.getServiceConfig()

        self.getLoggingService().debug(f"[{self.name}] serviceConfig: {config}")

        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise Exception("Could not connect to pigpiod")

        for s in config.get("sensors", []):
            pin = int(s.get("pin"))
            name = s.get("id")
            pull = pigpio.PUD_UP if s.get("pullUpOrDown", "up") == "up" else pigpio.PUD_DOWN
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

    def readState(self):
        """
        Returns the state of ALL sensors as dict.
        """
        sensorStates = {}
        if self.sensors:
            for sensor in self.sensors:
                pinState = self.pi.read(sensor["pin"])
                state = sensor["labelLow"] if pinState == 0 else sensor["labelHigh"]
                sensorStates[sensor["id"]] = state

        return sensorStates

    def publishState(self, mqttTopic: str, state):
        """
        Publishes each sensor independently based on change detection and updates the publishedState at the end.
        """

        publishNeccessary = True #self.state = None or self.publishIntervalExceeded()
        for sensor in self.sensors:
            singleSensorState = state[sensor["id"]]

            # skip if no change and publish time not exceeded yet
            if not publishNeccessary and sensor["lastState"] == singleSensorState:
                continue

            # Publish via parent logic
            super().publishState(sensor["mqttTopic"], singleSensorState)

            sensor["lastState"] = singleSensorState
        self.publishedState = state
