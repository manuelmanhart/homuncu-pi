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

        self._bits = []
        self._last_tick = 0
        self._reading = False

        # GPIO als Input mit Alert einrichten
        lgpio.gpio_claim_alert(self.h, self.gpio, lgpio.BOTH_EDGES)
        self._cb = lgpio.callback(self.h, self.gpio, lgpio.BOTH_EDGES, self._cb_handler)

    def _cb_handler(self, chip, gpio, level, tick):
        if not self._reading:
            return

        if level == 1:
            # Steigende Flanke: Startzeit merken
            self._last_tick = tick
        elif level == 0 and self._last_tick > 0:
            # Fallende Flanke: Pulsdauer berechnen
            # tick ist in Nanosekunden bei lgpio
            duration_us = (tick - self._last_tick) / 1000
            self._bits.append(1 if duration_us > 50 else 0)

    def trigger(self):
        if not self.powered:
            return

        if self.LED is not None:
            lgpio.gpio_write(self.h, self.LED, 1)

        self._bits = []
        self._last_tick = 0
        self._reading = False

        # Start-Signal senden
        lgpio.gpio_claim_output(self.h, self.gpio)
        lgpio.gpio_write(self.h, self.gpio, 0)
        time.sleep(0.018)

        # Auf Input umschalten und Alerts aktivieren
        lgpio.gpio_claim_alert(self.h, self.gpio, lgpio.BOTH_EDGES)
        self._reading = True

        # Warten bis Sensor fertig (max 5ms für 40 Bits)
        time.sleep(0.005)
        self._reading = False

        self._parse_bits()

    def _parse_bits(self):
        if len(self._bits) < 40:
            self.bad_CS += 1
            return

        bits = self._bits[:40]
        hH = hL = tH = tL = CS = 0

        for i, bit in enumerate(bits):
            if i < 8:
                hH = (hH << 1) | bit
            elif i < 16:
                hL = (hL << 1) | bit
            elif i < 24:
                tH = (tH << 1) | bit
            elif i < 32:
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

    def cancel(self):
        try:
            self._cb.cancel()
        except Exception:
            pass
        lgpio.gpiochip_close(self.h)
