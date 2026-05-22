from app.services.abstract_modular_base_service import AbstractModularBaseService
from app.services.base.mqtt_send_flags import MqttSendFlags
from pathlib import Path
import subprocess
import json
import time


class CameraService(AbstractModularBaseService):
    def __init__(self, registry):
        super().__init__("camera", registry)

    def onReady(self):
        config = self.getServiceConfig()
        self.resolution = config.get("resolution", [1920, 1080])
        self.quality = config.get("quality", 85)
        self.storage_path = Path(config.get("storagePath", "/tmp/camera"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        super().onReady()

    def readState(self) -> dict:
        return {
            "active": self.active,
            "storagePath": str(self.storage_path),
        }

    def onMqttMessage(self, message):
        action = message.get("action")
        if action == "capture":
            self._handle_capture()

    def _handle_capture(self):
        path = self._capture_image()
        if path is None:
            self._publish({
                "action": "capture",
                "success": False,
                "error": "capture failed",
            })
            return
        self._publish({
            "action": "capture",
            "success": True,
            "path": str(path),
        })

    def _capture_image(self) -> Path | None:
        timestamp = int(time.time())
        filename = f"capture_{timestamp}.jpg"
        filepath = self.storage_path / filename
        result = subprocess.run(
            [
                "libcamera-still",
                "-o", str(filepath),
                "--width", str(self.resolution[0]),
                "--height", str(self.resolution[1]),
                "--quality", str(self.quality),
                "--nopreview",
            ],
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            self.getLoggingService().error(
                self.name, f"libcamera-still failed: {result.stderr.decode()}"
            )
            return None
        return filepath

    def getMqttTopic(self) -> str:
        return self.getServiceConfig().get("mqttTopic", self.name)

    def _publish(self, state: dict):
        flags = self._get_mqtt_flags()
        topic = self.getMqttTopic()
        if MqttSendFlags.ADD_TIMESTAMP in flags:
            message = state
        else:
            message = json.dumps(state)
        self.getMqttService().sendMessage(topic, message, flags)

    def _get_mqtt_flags(self):
        raw = self.getServiceConfig().get("mqttFlags")
        if raw is not None:
            return MqttSendFlags.parse(raw)
        return (
            MqttSendFlags.ADD_BASE_TOPIC
            | MqttSendFlags.ADD_HOSTNAME
            | MqttSendFlags.ADD_TIMESTAMP
        )

    def activate(self) -> bool:
        self.active = True
        self.getLoggingService().info(self.name, "camera service activated")
        return True

    def deactivate(self) -> bool:
        self.active = False
        self.getLoggingService().info(self.name, "camera service deactivated")
        return True
