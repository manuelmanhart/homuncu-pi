import time
import lgpio

class sensor:
    MIN_INTERVAL = 2.0  # s, DHT22 darf nicht häufiger ausgelesen werden

    def __init__(self, gpio, sensor_type="DHT22", LED=None, power=None):
        self.gpio = gpio
        self.LED = LED
        self.power = power
        self.sensor_type = (sensor_type or "DHT22").upper()
        # DHT11 braucht >= 18 ms Startsignal, DHT22 reichen ~1-10 ms
        self.start_low = 0.020 if self.sensor_type == "DHT11" else 0.003

        self.rhum = -999
        self.temp = -999
        self.tov = None

        # Diagnose-Zähler
        self.bad_CS = 0
        self.short_frames = 0
        self.last_bit_count = 0
        self.last_error = None

        self._bits = []
        self._last_tick = 0
        self._last_cb = 0.0
        self._last_read = 0.0
        self._last_ok = False

        self.h = lgpio.gpiochip_open(0)
        try:
            if power is not None:
                lgpio.gpio_claim_output(self.h, power, 1)
                time.sleep(2)
            if LED is not None:
                lgpio.gpio_claim_output(self.h, LED, 0)
        except Exception:
            self.cancel()  # Handle nicht leaken
            raise

    def _cb_handler(self, chip, gpio, level, tick):
        self._last_cb = time.monotonic()
        if level == 1:
            self._last_tick = tick
        elif level == 0 and self._last_tick > 0:
            duration_us = (tick - self._last_tick) / 1000  # tick ist in ns
            self._bits.append(1 if duration_us > 50 else 0)
            self._last_tick = 0

    # Timing-kritisch: so wenig Code wie möglich zwischen Startsignal und Callback!
    def trigger(self):
        """Führt eine Messung durch. True = frische, gültige Werte, sonst False."""
        if self.h is None:
            return False

        # DHT22: nicht öfter als alle 2 s lesen -> sonst Ergebnis der letzten Messung
        if time.monotonic() - self._last_read < self.MIN_INTERVAL:
            return self._last_ok
        self._last_read = time.monotonic()
        self._last_ok = False
        self.last_error = None

        cb = None
        try:
            self._bits = []
            self._last_tick = 0
            self._last_cb = 0.0

            if self.LED is not None:
                lgpio.gpio_write(self.h, self.LED, 1)

            # Startsignal: Leitung low ziehen
            lgpio.gpio_claim_output(self.h, self.gpio, 0)
            time.sleep(self.start_low)

            # Sofort auf Eingang mit Flankenerkennung umschalten und Callback setzen
            lgpio.gpio_claim_alert(self.h, self.gpio, lgpio.BOTH_EDGES, lgpio.SET_PULL_UP)
            cb = lgpio.callback(self.h, self.gpio, lgpio.BOTH_EDGES, self._cb_handler)

            # Warten bis Frame komplett: >= 40 Bits und danach Ruhe auf der Leitung
            deadline = time.monotonic() + 0.1
            while time.monotonic() < deadline:
                time.sleep(0.001)
                if len(self._bits) >= 40 and time.monotonic() - self._last_cb > 0.003:
                    break
        except Exception as e:
            self.last_error = str(e)
            return False
        finally:
            if cb is not None:
                try:
                    cb.cancel()
                except Exception:
                    pass
            if self.LED is not None:
                try:
                    lgpio.gpio_write(self.h, self.LED, 0)
                except Exception:
                    pass

        self._last_ok = self._parse_bits(list(self._bits))
        return self._last_ok

    def _parse_bits(self, bits):
        self.last_bit_count = len(bits)

        # Erwartet: 40 Datenbits, evtl. +1 Antwort-Bit, +1 Störflanke am Anfang
        if not 40 <= len(bits) <= 42:
            self.short_frames += 1
            return False

        bits = bits[-40:]
        hH, hL, tH, tL, cs = [
            int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, 40, 8)
        ]

        if ((hH + hL + tH + tL) & 0xFF) != cs:
            self.bad_CS += 1
            return False

        if self.sensor_type == "DHT11":
            rhum = hH + hL * 0.1
            temp = tH + (tL & 0x7F) * 0.1
            if tL & 0x80:
                temp = -temp
        else:  # DHT22 / AM2302
            rhum = ((hH << 8) | hL) * 0.1
            temp = (((tH & 0x7F) << 8) | tL) * 0.1
            if tH & 0x80:
                temp = -temp

        if not (0 <= rhum <= 100 and -40 <= temp <= 80):
            self.bad_CS += 1
            return False

        self.rhum = rhum
        self.temp = temp
        self.tov = time.time()
        return True

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
        return self.short_frames

    def missing_message(self):
        return 0

    def sensor_resets(self):
        return 0

    def cancel(self):
        h, self.h = self.h, None  # idempotent
        if h is None:
            return
        try:
            if self.power is not None:
                lgpio.gpio_write(h, self.power, 0)  # Sensor stromlos (für Power-Cycle)
        except Exception:
            pass
        try:
            lgpio.gpiochip_close(h)
        except Exception:
            pass