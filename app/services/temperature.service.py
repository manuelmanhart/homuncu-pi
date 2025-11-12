import pigpio
import sys
import os
import subprocess
from app.services.abstract_sensor_service import AbstractSensorService
sys.path.append(os.path.dirname(__file__)) 
from app.services.temp_sensor import sensor

class TemperatureService(AbstractSensorService):
    def __init__(self, gpioPin=4, sensor_type="DHT22"):
        super().__init__("temperature")
        self.temperatureTolerance=self.config.get("temperatureTolerance", 0.5)
        self.humidityTolerance=self.config.get("humidityTolerance", 0.5)
        self.humidityCorrection40=self.config.get("humidityCorrection40", 0)
        self.humidityCorrection75=self.config.get("humidityCorrection75", 0)
        self.temperatureCorrection=self.config.get("temperatureCorrection", 0)
        self.gpioPin = gpioPin
        self.sensor_type = sensor_type

        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("Kann keine Verbindung zum pigpio daemon herstellen")
        self.sensor = sensor(self.pi, self.gpioPin)
        self.sensor.trigger()  # initial trigger

    def readNewState(self):
        try:
            print(f"sensor: {self.sensor}")
            if (self.sensor != None):
                print(f"reading sensor: {self.sensor}")
                self.sensor.trigger()
                import time; time.sleep(2)  # kurz warten auf Messung
                temperature = self.sensor.temperature()
                humidity = self.sensor.humidity()
                return {
                    "temperature": round(temperature + self.temperatureCorrection, 1),
                    "humidity": round(self.correctHumidity(humidity), 1),
                }
            else:
                print(f"sensor not ready yet")
                return { "Sensor not ready yet" }
        except Exception as e:
            return {"error": str(e)}

    def correctHumidity(self, humidity):
        if self.humidityCorrection40 > 0 and self.humidityCorrection75 > 0:
            return (humidity - self.humidityCorrection40) * (75 - self.humidityCorrection40) / (humidityCorrection75 - self.humidityCorrection40) + 40
        else:
            return humidity

    def hasSignificantChange(self, oldState, newState) -> bool:
        print(f"{oldState["temperature"]} - {newState["temperature"]} > {self.temperatureTolerance} or {oldState["humidity"]} - {newState["humidity"]} > {self.humidityTolerance}");
        return abs(oldState["temperature"] - newState["temperature"]) > self.temperatureTolerance or \
               abs(oldState["humidity"] - newState["humidity"]) > self.humidityTolerance;

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
        self.active = self.active and (result.returncode == 0 and result.stdout.strip() == "active")
        return self.active

    def install(self) -> bool:
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

    def uninstall(self) -> bool:
        self.sensor.cancel()
        self.pi.stop()
        return True
