import time

import bme680


class Bme680Sensor:
    _instances = {}

    @classmethod
    def get_instance(cls, i2c_addr=bme680.I2C_ADDR_PRIMARY):
        if i2c_addr not in cls._instances:
            cls._instances[i2c_addr] = cls(i2c_addr)
        return cls._instances[i2c_addr]

    def __init__(self, i2c_addr):
        self._sensor = bme680.BME680(i2c_addr)
        self._sensor.set_humidity_oversample(bme680.OS_2X)
        self._sensor.set_pressure_oversample(bme680.OS_4X)
        self._sensor.set_temperature_oversample(bme680.OS_8X)
        self._sensor.set_filter(bme680.FILTER_SIZE_3)
        self._sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
        self._sensor.set_gas_heater_temperature(320)
        self._sensor.set_gas_heater_duration(150)
        self._sensor.select_gas_heater_profile(0)
        self._data = None
        self._last_read = 0

    def read(self) -> bool:
        if self._sensor.get_sensor_data():
            self._data = self._sensor.data
            self._last_read = time.time()
            return True
        return False

    @property
    def temperature(self):
        return self._data.temperature if self._data else None

    @property
    def humidity(self):
        return self._data.humidity if self._data else None

    @property
    def pressure(self):
        return self._data.pressure if self._data else None

    @property
    def gas_resistance(self):
        return self._data.gas_resistance if self._data else None

    @property
    def last_read(self):
        return self._last_read

    def calculate_iaq(self, humidity=None, gas_resistance=None) -> float:
        hum = humidity if humidity is not None else self.humidity
        gas = gas_resistance if gas_resistance is not None else self.gas_resistance
        if hum is None or gas is None:
            return None
        humidity_bias = abs(hum - 40)
        iaq_raw = max(0.0, 500.0 - (gas / 1000.0) + humidity_bias * 3.0)
        return round(min(500.0, iaq_raw), 1)
