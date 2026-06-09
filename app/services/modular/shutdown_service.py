import subprocess
from gpiozero import Button
from app.services.abstract_sensor_service import AbstractSensorService

class ShutdownService(AbstractSensorService):
    def __init__(self, registry):
        super().__init__("shutdown", registry)
        self._shuttingDown = False
        self._button = None

    def onReady(self):
        config = self.getServiceConfig()
        self.viaMqtt = config.get("viaMqtt", False)
        self.viaButton = config.get("viaButton", False)
        self.pin = config.get("gpioPin", 3)

        self.getLoggingService().debug(self.name, f"serviceConfig: {config}")

        if self.viaButton:
            pull_up = config.get("pullDirection", "up") == "up"
            self._button = Button(self.pin, pull_up=pull_up)
            self._button.when_pressed = self._on_button_pressed

        super().onReady()

    def _on_button_pressed(self):
        if not self._shuttingDown:
            self._shuttingDown = True
            self.shutdown()

    def handleShutdownService(self):
        if self._button is not None:
            self._button.close()

    def readState(self):
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
