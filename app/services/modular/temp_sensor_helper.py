import time
import lgpio

class sensor:
    def __init__(self, gpio, sensor_type="DHT22", LED=None, power=None):
        self.gpio = gpio
        self.LED = LED
        self.power = power
        self.sensor_type = sensor_type

        self.h = lgpio.gpiochip_open(0)

        if power is not None:
            lgpio.gpio_claim_output(self.h, power)
            lgpio.gpio_write(self.h, power, 1)
            time.sleep(2)

        if LED is not None:
            lgpio.gpio_claim_output(self.h, LED)

        self.powered = True
        self.bad_CS = 0
        self.rhum = -999
        self.temp = -999
        self.tov = None

    def temperature(self):
        return self.temp

    def humidity(self):
        return self.rhum

    def staleness(self):
        if self.tov is not None:
            return time.time() - self.tov
        return -999

    def bad_checksum(self):
        return self.bad_CS

    def short_message(self):
        return 0

    def missing_message(self):
        return 0

    def sensor_resets(self):
        return 0

    def trigger(self):
        if not self.powered:
            return

        if self.LED is not None:
            lgpio.gpio_write(self.h, self.LED, 1)

        lgpio.gpio_claim_output(self.h, self.gpio)
        lgpio.gpio_write(self.h, self.gpio, lgpio.LOW)
        time.sleep(0.018)
        lgpio.gpio_claim_input(self.h, self.gpio, lgpio.SET_PULL_NONE)

        try:
            self._read_sensor()
        except Exception:
            self.bad_CS += 1

    def _read_sensor(self):
        timeout = time.time() + 0.1

        while lgpio.gpio_read(self.h, self.gpio) == 1:
            if time.time() > timeout:
                return

        while lgpio.gpio_read(self.h, self.gpio) == 0:
            if time.time() > timeout:
                return

        hH = hL = tH = tL = CS = 0

        for bit_idx in range(40):
            while lgpio.gpio_read(self.h, self.gpio) == 0:
                if time.time() > timeout:
                    return

            start = time.perf_counter_ns()
            while lgpio.gpio_read(self.h, self.gpio) == 1:
                if time.time() > timeout:
                    return
            duration = (time.perf_counter_ns() - start) / 1000

            bit = 1 if duration > 50 else 0

            if bit_idx < 8:
                hH = (hH << 1) | bit
            elif bit_idx < 16:
                hL = (hL << 1) | bit
            elif bit_idx < 24:
                tH = (tH << 1) | bit
            elif bit_idx < 32:
                tL = (tL << 1) | bit
            else:
                CS = (CS << 1) | bit

        total = hH + hL + tH + tL
        if (total & 0xFF) == CS:
            self.rhum = ((hH << 8) | hL) * 0.1
            if tH & 0x80:
                self.temp = -(((tH & 0x7F) << 8) | tL) * 0.1
            else:
                self.temp = ((tH << 8) | tL) * 0.1
            self.tov = time.time()
            if self.LED is not None:
                lgpio.gpio_write(self.h, self.LED, 0)
        else:
            self.bad_CS += 1

    def cancel(self):
        lgpio.gpiochip_close(self.h)
