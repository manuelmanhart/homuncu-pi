import subprocess
import pigpio
from app.services.abstract_sensor_service import AbstractSensorService


class ShutdownService(AbstractSensorService):
    def __init__(self, registry):
        super().__init__("shutdown", registry)
        self._shuttingDown = False

    def onReady(self):
        config = self.getServiceConfig()
        self.viaMqtt = config.get("viaMqtt", False)
        self.viaButton = config.get("viaButton", False)
        self.pin = config.get("gpioPin", 3)

        self.getLoggingService().debug(self.name, f"serviceConfig: {config}")

        if self.viaButton:
            self.pi = pigpio.pi()
            if not self.pi.connected:
                raise Exception("Could not connect to pigpiod")
            pull = pigpio.PUD_UP if config.get("pullDirection", "up") == "up" else pigpio.PUD_DOWN
            self.pi.set_mode(self.pin, pigpio.INPUT)
            self.pi.set_pull_up_down(self.pin, pull)

        super().onReady()

    def handleShutdownService(self):
        if self.viaButton:
            self.pi.stop()

    def readState(self):
        if self.viaButton and not self._shuttingDown:
            if self.pi.read(self.pin) == 0:
                self._shuttingDown = True
                self.shutdown()
        return {
            "active": self.active,
            "viaButton": self.viaButton,
            "viaMqtt": self.viaMqtt,
        }

    def onMqttMessage(self, message):
        if not self.active or not self.viaMqtt or self._shuttingDown:
            return
        action = message.get("action")
        if action == "shutdown":
            self.getLoggingService().info(self.name, "shutdown via mqtt triggered")
            self._shuttingDown = True
            self.shutdown()

    def shutdown(self) -> bool:
        result = subprocess.run(
            ["sudo", "shutdown", "now"],
            capture_output=True,
            text=True,
        ).returncode
        return result == 0
