import time
from app.services.abstract_sensor_service import AbstractSensorService
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
        self.sensor = sensor(self.gpioPin, self.sensor_type)
        super().onReady()

    def restartSensor(self):
        if self.sensor is not None:
            try:
                self.sensor.cancel()
            except Exception:
                pass
            time.sleep(3)
        self.sensor = sensor(self.gpioPin, self.sensor_type)

    def readState(self):
        try:
            if self.sensor is not None:
                self.sensor.trigger()
                time.sleep(0.2)
                temperature = self.sensor.temperature()
                humidity = self.sensor.humidity()
                staleness = self.sensor.staleness()

                if temperature <= -999 or humidity <= -999 or staleness > 60:
                    self.getLoggingService().warn(self.name, f"Invalid reading (temp={temperature}, hum={humidity}, staleness={staleness}s) - restarting sensor")
                    self.restartSensor()
                    return {"error": "Sensor restarted, retry on next cycle"}

                return {
                    "temperature": round(self.correctTemperature(temperature), 1),
                    "humidity": round(self.correctHumidity(humidity), 1),
                }
            else:
                return {"error": "Sensor not ready yet"}
        except Exception as e:
            return {"error": str(e)}

    def correctTemperature(self, temperature):
        if self.temperatureCorrection != 0:
            return temperature + self.temperatureCorrection
        return temperature

    def correctHumidity(self, humidity):
        if self.humidityCorrection40 != 0 and self.humidityCorrection75 != 0:
            return (humidity - self.humidityCorrection40) * (75 - self.humidityCorrection40) / (self.humidityCorrection75 - self.humidityCorrection40) + 40
        return humidity

    def handleShutdownService(self):
        if self.sensor is not None:
            self.sensor.cancel()

    def hasSignificantChange(self, oldState, newState) -> bool:
        if newState.get("humidity", 0) > 0:
            tempOver = self.isOverThreshold(oldState["temperature"], newState["temperature"], self.temperatureTolerance)
            humOver = self.isOverThreshold(oldState["humidity"], newState["humidity"], self.humidityTolerance)
            return tempOver or humOver
        return False

    def isOverThreshold(self, a, b, tolerance):
        return abs(a - b) > tolerance

    def isServiceActive(self) -> bool:
        return self.active

    def install(self) -> bool:
        return True

    def uninstall(self) -> bool:
        if self.sensor is not None:
            self.sensor.cancel()
        return True
