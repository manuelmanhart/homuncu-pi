from app.services.abstract_sensor_service import AbstractSensorService
from app.services.modular.bme680_sensor_helper import Bme680Sensor


class AirQualityService(AbstractSensorService):
    def __init__(self, registry):
        super().__init__("airQuality", registry)

    def onReady(self):
        config = self.getServiceConfig()
        self.gasTolerance = config.get("gasTolerance", 10000)
        self.i2c_addr = int(config.get("i2cAddr", "0x76"), 16)
        self.sensor = Bme680Sensor.get_instance(self.i2c_addr)
        super().onReady()

    def readState(self):
        if not self.sensor.read():
            return {"error": "BME680 read failed"}
        gas = self.sensor.gas_resistance
        pressure = self.sensor.pressure
        humidity = self.sensor.humidity
        if gas is None or pressure is None:
            return {"error": "BME680 returned no data"}
        iaq = self.sensor.calculate_iaq(humidity, gas)
        return {
            "pressure": round(pressure, 1),
            "gas_resistance": gas,
            "iaq": iaq,
        }

    def hasSignificantChange(self, oldState, newState) -> bool:
        if newState.get("gas_resistance", 0) > 0:
            return self.isOverThreshold(
                oldState.get("gas_resistance", 0),
                newState["gas_resistance"],
                self.gasTolerance,
            )
        return False

    def isOverThreshold(self, a, b, tolerance):
        return abs(a - b) > tolerance
