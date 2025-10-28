import pigpio
import sys
import os
import subprocess
from app.services.abstract_sensor_service import AbstractSensorService
sys.path.append(os.path.dirname(__file__)) 
from app.services.temp_sensor import sensor
from datetime import datetime

class TemperatureService(AbstractSensorService):
    def __init__(self, gpio_pin=4, sensor_type="DHT22"):
        super().__init__("temperature")
        cfg = self.getServiceConfig()
#        self.pollInterval=cfg.get("pollInterval", 30),
        self.tolerance=cfg.get("temperatureTolerance", 0.5)
        self.humidityTolerance=cfg.get("humidityTolerance", 0.5)
        self.gpio_pin = gpio_pin
        self.sensor_type = sensor_type
        self.last_temp = None
        self.last_humidity = None
        self.last_read = None

        if not self.isServiceActive():
            self.activate()

        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("Kann keine Verbindung zum pigpio daemon herstellen")
        self.sensor = sensor(self.pi, self.gpio_pin)
        self.sensor.trigger()  # initial trigger
        self.start()

    def readState(self):
        try:
            self.sensor.trigger()
            import time; time.sleep(2)  # kurz warten auf Messung
            self.last_temp = self.sensor.temperature()
            self.last_humidity = self.sensor.humidity()
            self.last_read = datetime.now().isoformat()
            return {
                "temperature": self.last_temp,
                "humidity": self.last_humidity,
                "timestamp": self.last_read
            }
        except Exception as e:
            return {"error": str(e)}

    def initStatus(self) -> bool:
#        self.installed = True
#        self.active = False
        return True

    def isServiceActive(self) -> bool:
        result = subprocess.run(
            ["systemctl", "is-enabled", "pigpiod"],
            capture_output=True,
            text=True
        )
        self.installed = (result.returncode == 0)
        result = subprocess.run(
            ["systemctl", "is-active", "pigpiod"],
            capture_output=True,
            text=True
        )
        self.active = (result.returncode == 0 and result.stdout.strip() == "active")
        return self.active

    def updateState(self) -> dict:
        """Liest temperatur und luftfeuchte aus"""
        now = datetime.now()

        return {
            "date": now.strftime("%Y-%m-%d"), # 2025-09-19
            "time": now.strftime("%H:%M:%S"), # 18:30:15
            self.name: self.readState()
        }

    def activate(self) -> bool:
        result = subprocess.run(
            ["apt", "update"],
            capture_output=True,
            text=True
        )
        result = subprocess.run(
            ["apt", "install", "-y", "pigpio"],
            capture_output=True,
            text=True
        )
        result = subprocess.run(
            ["systemctl", "enable", "pigpiod"],
            capture_output=True,
            text=True
        )
        result = subprocess.run(
            ["systemctl", "start", "pigpiod"],
            capture_output=True,
            text=True
        )
        return (result.returncode == 0)

    def deactivate(self) -> bool:
        self.sensor.cancel()
        self.pi.stop()
        return True

    def configure(self, config: dict) -> bool:
        self.config.update(config)
        return True
