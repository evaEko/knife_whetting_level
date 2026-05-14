from machine import I2C, Pin
from drivers.ssd1306 import Display

_BLE      = 'BLE'
_BLE_LIVE = 'BLE*'


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

    def show_splash(self, word):
        """Render a single word as large as possible, centred on the full display."""
        d = self._display
        d.fill(0)
        scale = 2
        char_pitch = 7
        # width = (len-1)*char_pitch*scale + 8*scale
        w = ((len(word) - 1) * char_pitch + 8) * scale
        x = max(0, (d.width - w) // 2)
        y = (d.height - 8 * scale) // 2
        d.large_text(word, x, y, scale=scale, char_pitch=char_pitch)
        d.show()

    def show_text(self, *lines):
        d = self._display
        d.fill(0)
        for i, line in enumerate(lines[:5]):
            d.text(str(line), 0, i * 8, 1)
        d.show()

    def show_option(self, label, subtitle=None):
        """Single-item selector: label and optional subtitle centered."""
        d = self._display
        d.fill(0)
        y = 8 if subtitle else 16
        d.text(label, max(0, (d.width - len(label) * 8) // 2), y, 1)
        if subtitle is not None:
            d.text(subtitle, max(0, (d.width - len(subtitle) * 8) // 2), 24, 1)
        d.show()

    def show_measurement(self, pitch, target_str, ble, ble_connected=False):
        indicators = [target_str] if target_str is not None else []
        if ble:
            indicators.append(_BLE_LIVE if ble_connected else _BLE)
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
                if item == _BLE or item == _BLE_LIVE:
                    d.ble_icon(cursor, 33)
                    cursor += 6
                    if item == _BLE_LIVE:
                        d.text('*', cursor, 32, 1)
                        cursor += 10
                else:
                    d.text(str(item), cursor, 32, 1)
                    cursor += len(str(item)) * 8 + 2
        d.show()

    def show_battery(self, pct):
        d = self._display
        d.fill(0)
        if pct is None:
            d.text("To charge", 0, 0, 1)
            d.large_text("PLUG", 8, 12, scale=2, char_pitch=7)
            d.text("low=pass", 0, 32, 1)
        else:
            d.text("BAT", (72 - 24) // 2, 2, 1)
            pct_str = "{}%".format(pct)
            pw = len(pct_str) * 16
            d.large_text(pct_str, (72 - pw) // 2, 14, scale=2)
            bx, by, bw, bh = 6, 33, 60, 5
            d.fb.rect(bx, by, bw, bh, 1)
            filled = int(bw * pct / 100)
            if filled > 0:
                d.fb.fill_rect(bx, by, filled, bh, 1)
        d.show()

    def show_ble_status(self, connected, enabled):
        if connected:
            status = "connected"
        elif enabled:
            status = "connecting"
        else:
            status = "Off"
        d = self._display
        d.fill(0)
        scale = 1
        w = ((len(status) - 1) * 7 + 8) * scale
        x = max(0, (d.width - w) // 2)
        y = max(0, (d.height - 8 * scale) // 2 - 4)
        d.large_text(status, x, y, scale=scale, char_pitch=7)
        d.text("top:tgl  low:back", 0, 32, 1)
        d.show()

    def clear(self):
        self._display.fill(0)
        self._display.show()

    def invert(self, on):
        self._display.invert(on)