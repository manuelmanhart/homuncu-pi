import pigpio
import sys
import os
import subprocess
import time
from app.services.abstract_sensor_service import AbstractSensorService
sys.path.append(os.path.dirname(__file__)) 
from app.services.modular.temp_sensor_helper import sensor

# TemperatureService
# ------
# Reads a DHT22 (or configurable) temperature/humidity sensor via pigpio and publishes changes.
# Config keys (under services.temperature):
#   gpioPin (int) - GPIO pin number (default 4).
#   sensorType (str) - sensor model, (default "DHT22") - currently supported "DHT11", "DHT22" and "".
#   temperatureTolerance / humidityTolerance (float) - thresholds for significant change.
#   temperatureCorrection, humidityCorrection40, humidityCorrection75 (float) - optional calibration offsets.
# MQTT: Publishes temperature/humidity readings on the configured `mqttTopic` (default service name) using flags ADD_BASE_TOPIC|ADD_HOSTNAME|ADD_TIMESTAMP.
class TemperatureService(AbstractSensorService):
    def __init__(self, registry):
        super().__init__("temperature", registry)

    def onReady(self):
        self.temperatureTolerance = self.getServiceConfig().get("temperatureTolerance", 0.5)
        self.humidityTolerance = self.getServiceConfig().get("humidityTolerance", 3)
        self.humidityCorrection40 = self.getServiceConfig().get("humidityCorrection40", 0)
        self.humidityCorrection75 = self.getServiceConfig().get("humidityCorrection75", 0)
        self.temperatureCorrection = self.getServiceConfig().get("temperatureCorrection", 0)
        self.gpioPin = self.getServiceConfig().get("gpioPin", 4)
        self.sensor_type = self.getServiceConfig().get("sensorType", "DHT22")
        self.pi = None

        self.ensureConnected()
        super().onReady()

    def restartSensor(self):
        if (self.sensor != None):
            try:
                self.sensor.cancel()
            except Exception:
                pass
            time.sleep(3)  # DHT22 braucht Zeit zum Erholen
        self.sensor = sensor(self.pi, self.gpioPin)

    def ensureConnected(self):
        if self.pi == None or not self.pi.connected:
            self.getLoggingService().warn(self.name, "pigpio not connected, reconnect...")
            try:
                self.pi.stop()
            except Exception:
                pass
            self.pi = pigpio.pi()
            if not self.pi.connected:
                self.getLoggingService().error(self.name, "could not connect to pigpio")
                self.deactivate()
                raise RuntimeError("pigpio (re)connect unsuccessful")
            self.getLoggingService().debug(self.name, "pigpio connected")
            self.sensor = sensor(self.pi, self.gpioPin)
            self.sensor.trigger()

    def readState(self):
        self.ensureConnected()
        try:
            self.getLoggingService().debug(self.name, f" reading sensor: {self.sensor}")
            if (self.sensor != None):
                self.sensor.trigger()
                time.sleep(2.5)  # kurz warten auf Messung
                temperature = self.sensor.temperature()
                humidity = self.sensor.humidity()
                staleness = self.sensor.staleness()
                self.getLoggingService().debug(
                    self.name,
                    f"Sensor-Stats: bad_CS={self.sensor.bad_checksum()}, "
                    f"bad_SM={self.sensor.short_message()}, "
                    f"bad_MM={self.sensor.missing_message()}, "
                    f"staleness={self.sensor.staleness():.1f}s"
                )
                # -999 explizit abfangen
                if temperature <= -999 or humidity <= -999 or staleness > 60:
                    self.getLoggingService().warn(self.name, f"Ungültige Messung (temp={temperature}, hum={humidity}, staleness={staleness}s) - Sensor wird neu initialisiert")
                    self.restartSensor()
                    return {"error": "Sensor restarted, retry on next cycle"}

                self.getLoggingService().debug(self.name, f" read temp {temperature} read hum {humidity}")
                self.getLoggingService().debug(self.name, f" corrected temp {self.correctTemperature(temperature)} corrected hum {self.correctHumidity(humidity)}")
                self.getLoggingService().debug(self.name, f" rounded temp {round(self.correctTemperature(temperature), 1)} rounded hum {round(self.correctHumidity(humidity), 1)}")
                return {
                    "temperature": round(self.correctTemperature(temperature), 1),
                    "humidity": round(self.correctHumidity(humidity), 1),
                }
            else:
                self.getLoggingService().warn(self.name, f" sensor not ready yet")
                return { "error": "Sensor not ready yet" }
        except Exception as e:
            return {"error": str(e)}

    def correctTemperature(self, temperature):
        if self.temperatureCorrection != 0:
            return (temperature + self.temperatureCorrection)
        else:
            return temperature

    def correctHumidity(self, humidity):
        if self.humidityCorrection40 != 0 and self.humidityCorrection75 != 0:
            return (humidity - self.humidityCorrection40) * (75 - self.humidityCorrection40) / (humidityCorrection75 - self.humidityCorrection40) + 40
        else:
            return humidity

    def hasSignificantChange(self, oldState, newState) -> bool:
        if (newState["humidity"] > 0):
            tempOverThreshold = self.isOverThreshold(oldState["temperature"], newState["temperature"], self.temperatureTolerance)
            humOverThreshold = self.isOverThreshold(oldState["humidity"], newState["humidity"], self.humidityTolerance)
            return tempOverThreshold or humOverThreshold
        else:
            return False

    def isOverThreshold(self, numberA, numberB, tolerance):
        result = abs(numberA - numberB) > tolerance
        self.getLoggingService().debug(self.name, f" isOverThreshold({numberA}, {numberB}, {tolerance}) => {result}")
        return result

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
