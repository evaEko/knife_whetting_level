from machine import I2C, Pin
from drivers.ssd1306 import Display


class DisplayService:
    def __init__(self, sda_pin, scl_pin, i2c_id, addr):
        self._sda_pin = sda_pin
        self._scl_pin = scl_pin
        self._i2c_id  = i2c_id
        self._addr    = addr
        self._display = None

    def init(self):
        i2c = I2C(self._i2c_id,
                  sda=Pin(self._sda_pin),
                  scl=Pin(self._scl_pin),
                  freq=400_000)
        self._display = Display(i2c, addr=self._addr)

    def show_text(self, *lines):
        d = self._display
        d.fill(0)
        for i, line in enumerate(lines[:5]):
            d.text(str(line), 0, i * 8, 1)
        d.show()

    def show_option(self, label, subtitle=None):
        """Single-item selector: label large, optional subtitle small below."""
        d = self._display
        d.fill(0)
        d.large_text(label, 0, 4, scale=2)
        if subtitle is not None:
            d.text(subtitle, 0, 32, 1)
        d.show()

    def show_measurement(self, pitch, target_str, ble):
        indicators = [target_str] if target_str is not None else []
        if ble:
            indicators.append("BLE")
        self.show_angle("{:.1f}".format(pitch), *indicators)

    def show_angle(self, angle_str, *indicators):
        """Large centred angle in top 32px, small indicator row in bottom 8px.
        Pass the sentinel string 'BLE' in indicators to draw the BLE icon glyph.
        """
        d = self._display
        d.fill(0)
        scale = 2
        x = (d.width - len(angle_str) * 8 * scale) // 2
        y = (32 - 8 * scale) // 2
        d.large_text(angle_str, x, y, scale=scale)
        if indicators:
            cursor = 0
            for item in indicators:
                if item == 'BLE' or item == 'BLE*':
                    d.ble_icon(cursor, 33)
                    cursor += 6
                    if item == 'BLE*':
                        d.text('*', cursor, 32, 1)
                        cursor += 10
                else:
                    d.text(str(item), cursor, 32, 1)
                    cursor += len(str(item)) * 8 + 2
        d.show()

    def clear(self):
        self._display.fill(0)
        self._display.show()

    def invert(self, on):
        self._display.invert(on)