import time
from app.services.abstract_sensor_service import AbstractSensorService
from app.services.modular.bme680_sensor_helper import Bme680Sensor as Bme680SensorHelper
from app.services.modular.temp_sensor_helper import sensor as DhtSensor

# TemperatureService
# ------
# Reads a DHT22 (or configurable) temperature/humidity sensor via pigpio and publishes changes.
# Config keys (under services.temperature):
#   gpioPin (int) - GPIO pin number (default 4).
#   sensorType (str) - sensor model, (default "DHT22") - currently supported "DHT11", "DHT22" and "".
#   temperatureTolerance / humidityTolerance (float) - thresholds for significant change.
#   temperatureCorrection, humidityCorrection40, humidityCorrection75 (float) - optional calibration offsets.
#   minTemp, maxTemp (float) - absolute bounds for temperature; readings outside are ignored.
#   minHumidity, maxHumidity (float) - absolute bounds for humidity; readings outside are ignored.
#   maxPlausibleTempChange, maxPlausibleHumidityChange (float) - max change from last valid reading; implausible spikes are ignored.
# MQTT: Publishes temperature/humidity readings on the configured `mqttTopic` (default service name) using flags ADD_BASE_TOPIC|ADD_HOSTNAME|ADD_TIMESTAMP.
class TemperatureService(AbstractSensorService):
    def __init__(self, registry):
        super().__init__("temperature", registry)
        self._bme680 = False
        self._lastValidReading = None
        self.sensor = None
        self._failCount = 0
        self._pendingOutlier = None
        self._outlierCount = 0

    def onReady(self):
        self.temperatureTolerance = self.getServiceConfig().get("temperatureTolerance", 0.5)
        self.humidityTolerance = self.getServiceConfig().get("humidityTolerance", 3)
        self.humidityCorrection40 = self.getServiceConfig().get("humidityCorrection40", 0)
        self.humidityCorrection75 = self.getServiceConfig().get("humidityCorrection75", 0)
        self.temperatureCorrection = self.getServiceConfig().get("temperatureCorrection", 0)
        self.gpioPin = self.getServiceConfig().get("gpioPin", 4)
        self.sensor_type = self.getServiceConfig().get("sensorType", "DHT22")
        self.minTemp = self.getServiceConfig().get("minTemp", None)
        self.maxTemp = self.getServiceConfig().get("maxTemp", None)
        self.maxPlausibleTempChange = self.getServiceConfig().get("maxPlausibleTempChange", None)
        self.minHumidity = self.getServiceConfig().get("minHumidity", None)
        self.maxHumidity = self.getServiceConfig().get("maxHumidity", None)
        self.maxPlausibleHumidityChange = self.getServiceConfig().get("maxPlausibleHumidityChange", None)

        self.powerPin = self.getServiceConfig().get("powerPin", None)            # optional: Sensor-VCC über GPIO/MOSFET
        self.maxFailures = self.getServiceConfig().get("maxConsecutiveFailures", 5)
        self.readRetries = self.getServiceConfig().get("readRetries", 2)         # Versuche pro Zyklus
        self.outlierAcceptCount = self.getServiceConfig().get("outlierAcceptCount", 3)

        if self.sensor_type == "BME680":
            self.restartBme()
        else:
            self._createSensor()
            self.restartDht()

        super().onReady()

    def restartBme(self):
        self._bme680 = True
        i2c_addr = int(self.getServiceConfig().get("i2cAddr", "0x76"), 16)
        self.bme_sensor = Bme680SensorHelper.get_instance(i2c_addr)

    def restartDht(self):
        if self.sensor is not None:
            try:
                self.sensor.cancel()
            except Exception:
                pass
            self.sensor = None
            time.sleep(3)
        try:
            self.sensor = DhtSensor(self.gpioPin, self.sensor_type)
        except Exception as e:
            self.getLoggingService().error(self.name, f"DHT sensor could not be initialized {str(e)}...")
            pass

    def _read_bme680(self):
        if not self.bme_sensor.read():
            return {"error": "BME680 read failed"}
        temperature = self.bme_sensor.temperature
        humidity = self.bme_sensor.humidity
        pressure = self.bme_sensor.pressure
        if temperature is None or humidity is None:
            return {"error": "BME680 returned no data"}
        result = {
            "temperature": round(self.correctTemperature(temperature), 1),
            "humidity": round(self.correctHumidity(humidity), 1),
            "pressure": round(pressure, 1),
        }
        return result

    def _createSensor(self):
        try:
            self.sensor = DhtSensor(self.gpioPin, self.sensor_type, power=self.powerPin)
            return True
        except Exception as e:
            self.sensor = None  # kein totes Objekt behalten
            self.getLoggingService().warn(self.name, f"Sensor init failed: {e}")
            return False

    def restartSensor(self):
        if self._bme680:
            return
        old, self.sensor = self.sensor, None
        if old is not None:
            try:
                old.cancel()
            except Exception:
                pass
        time.sleep(3)
        self._createSensor()

    def _read_dht(self):
        if self.sensor is None and not self._createSensor():
            return {"error": "Sensor init failed, retry on next cycle"}

        ok = False
        for attempt in range(self.readRetries):
            try:
                ok = self.sensor.trigger()
            except Exception as e:
                self.getLoggingService().warn(self.name, f"trigger failed: {e}")
                ok = False
            if ok:
                break
            if attempt < self.readRetries - 1:
                time.sleep(self.sensor.MIN_INTERVAL + 0.1)

        if not ok:
            self._failCount += 1
            s = self.sensor
            msg = (f"DHT read failed ({self._failCount}/{self.maxFailures}, bits={s.last_bit_count}, "
                f"short={s.short_frames}, badCS={s.bad_CS}, err={s.last_error})")
            if self._failCount >= self.maxFailures:
                self.getLoggingService().warn(self.name, msg + " - restarting sensor")
                self._failCount = 0
                self.restartSensor()
            return {"error": msg}

        self._failCount = 0
        return {
            "temperature": round(self.correctTemperature(self.sensor.temperature()), 1),
            "humidity": round(self.correctHumidity(self.sensor.humidity()), 1),
        }

    def readState(self):
        try:
            result = self._read_bme680() if self._bme680 else self._read_dht()

            if "error" not in result:
                if not self._isWithinAbsoluteBounds(result):
                    self.getLoggingService().warn(self.name, f"Reading out of bounds: {result}")
                    return {"error": "Reading out of bounds"}

                if self._isPlausibleChange(result):
                    self._pendingOutlier = None
                    self._outlierCount = 0
                elif self._acceptAsNewBaseline(result):
                    self.getLoggingService().warn(self.name, f"Accepting {result} as new baseline")
                else:
                    self.getLoggingService().warn(self.name, f"Implausible change: {result}")
                    return {"error": "Implausible change"}

                self._lastValidReading = result
            return result
        except Exception as e:
            return {"error": str(e)}

    def _acceptAsNewBaseline(self, reading):
        # Mehrere "unplausible" Werte, die untereinander konsistent sind -> echte Änderung
        p = self._pendingOutlier
        if p is not None and self._isPlausibleChange(reading, p):
            self._outlierCount += 1
        else:
            self._outlierCount = 1
        self._pendingOutlier = reading
        if self._outlierCount >= self.outlierAcceptCount:
            self._pendingOutlier = None
            self._outlierCount = 0
            return True
        return False

    def _isPlausibleChange(self, reading, ref=None):
        ref = ref if ref is not None else self._lastValidReading
        if ref is None:
            return True
        temp, hum = reading.get("temperature"), reading.get("humidity")
        refTemp, refHum = ref.get("temperature"), ref.get("humidity")
        if temp is not None and refTemp is not None:
            if self.maxPlausibleTempChange is not None and abs(temp - refTemp) > self.maxPlausibleTempChange:
                return False
        if hum is not None and refHum is not None:
            if self.maxPlausibleHumidityChange is not None and abs(hum - refHum) > self.maxPlausibleHumidityChange:
                return False
        return True

    def hasSignificantChange(self, oldState, newState) -> bool:
        if "temperature" not in oldState or "humidity" not in oldState:
            return True
        if newState.get("humidity", 0) > 0:
            return (self.isOverThreshold(oldState["temperature"], newState["temperature"], self.temperatureTolerance)
                    or self.isOverThreshold(oldState["humidity"], newState["humidity"], self.humidityTolerance))
        return False

    def correctTemperature(self, temperature):
        if self.temperatureCorrection != 0:
            return temperature + self.temperatureCorrection
        return temperature

    def correctHumidity(self, humidity):
        if self.humidityCorrection40 != 0 and self.humidityCorrection75 != 0:
            return (humidity - self.humidityCorrection40) * (75 - self.humidityCorrection40) / (self.humidityCorrection75 - self.humidityCorrection40) + 40
        return humidity

    def _isWithinAbsoluteBounds(self, reading):
        temp = reading.get("temperature")
        hum = reading.get("humidity")
        if temp is not None:
            if self.minTemp is not None and temp < self.minTemp:
                return False
            if self.maxTemp is not None and temp > self.maxTemp:
                return False
        if hum is not None:
            if self.minHumidity is not None and hum < self.minHumidity:
                return False
            if self.maxHumidity is not None and hum > self.maxHumidity:
                return False
        return True

    def handleShutdownService(self):
        if self._bme680:
            return
        if self.sensor is not None:
            self.sensor.cancel()

    def isOverThreshold(self, a, b, tolerance):
        return abs(a - b) > tolerance

    def isServiceActive(self) -> bool:
        return self.active

    def install(self) -> bool:
        return True

    def uninstall(self) -> bool:
        if self._bme680:
            return True
        if self.sensor is not None:
            self.sensor.cancel()
        return True
