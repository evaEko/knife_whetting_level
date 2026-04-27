from machine import I2C, Pin
from config import SDA_OLED, SCK_OLED, OLED_ADDR
from drivers.ssd1306 import SSD1306


class Display:
    def __init__(self):
        self._oled = None

    def init(self):
        if self._oled is not None:
            return
        try:
            self._oled = SSD1306(
                I2C(1, sda=Pin(SDA_OLED), scl=Pin(SCK_OLED), freq=400000),
                addr=OLED_ADDR
            )
            print("OLED OK")
        except Exception as e:
            print(f"OLED ERROR: {e}")

    @property
    def ready(self):
        return self._oled is not None

    def invert(self, on):
        if self._oled:
            self._oled.invert(on)

    # --- boot ---

    def show_knife(self):
        oled = self._oled
        if not oled:
            return
        oled.fill(0)
        fb = oled.fb
        fb.fill_rect(2, 15, 14, 10, 1)
        fb.fill_rect(4, 17, 3, 6, 0)
        fb.fill_rect(10, 17, 3, 6, 0)
        fb.fill_rect(17, 11, 3, 18, 1)
        for x in range(20, 70):
            spine_y = 16 + (x - 20) * 3 // 49
            edge_y  = 22 - (x - 20) * 3 // 49
            fb.vline(x, spine_y, edge_y - spine_y + 1, 1)
        fb.pixel(70, 19, 1)
        oled.show()

    # --- battery ---

    def show_battery(self, pct):
        oled = self._oled
        if not oled:
            return
        oled.fill(0)
        if pct is None:
            oled.text("Turn on", 8, 0, 1)
            oled.text("to charge", 0, 10, 1)
            oled.text("low=", 0, 22, 1)
            oled.text("bypass", 0, 32, 1)
        else:
            oled.text("BAT", (72 - 24) // 2, 2, 1)
            pct_str = f"{pct}%"
            pw = len(pct_str) * 16
            oled.large_text(pct_str, (72 - pw) // 2, 14, scale=2)
            bx, by, bw, bh = 6, 33, 60, 5
            oled.fb.rect(bx, by, bw, bh, 1)
            filled = int(bw * pct / 100)
            if filled > 0:
                oled.fb.fill_rect(bx, by, filled, bh, 1)
        oled.show()

    # --- angle ---

    def show_angle(self, angle, label=None, fmt="1d_half"):
        oled = self._oled
        if not oled:
            return
        oled.fill(0)
        self._draw_angle_band(angle, fmt, y=4 if label else 12)
        if label:
            oled.text(label, 0, 24, 1)
        oled.show()

    def update_angle(self, angle, fmt="1d_half"):
        """Redraw only the angle band — avoids flickering static UI elements."""
        oled = self._oled
        if not oled:
            return
        oled.fb.fill_rect(0, 12, 72, 16, 0)
        self._draw_angle_band(angle, fmt, y=12)
        oled.show()

    # --- messages ---

    def show_message(self, *lines):
        """Show up to 5 lines of small text, evenly spaced."""
        oled = self._oled
        if not oled:
            return
        oled.fill(0)
        for i, line in enumerate(lines):
            oled.text(line, 0, i * 10, 1)
        oled.show()

    def show_error(self, msg):
        oled = self._oled
        if not oled:
            return
        oled.fill(0)
        oled.text("ERROR:", 0, 0, 1)
        oled.text(msg[:16], 0, 12, 1)
        oled.show()

    def show_calibration(self, angle, fmt="1d_half"):
        """Calibration screen: top hint, angle, bottom hint."""
        oled = self._oled
        if not oled:
            return
        oled.fill(0)
        oled.text("top=esc", 0, 0, 1)
        oled.text("low=ok", 8, 32, 1)
        self._draw_angle_band(angle, fmt, y=12)
        oled.show()

    def show_preset(self, name, angle):
        oled = self._oled
        if not oled:
            return
        oled.fill(0)
        oled.text(name[:16], 0, 0, 1)
        oled.large_text(f"{angle:.0f}", 0, 12, scale=2)
        oled.text("low=set  top=next", 0, 32, 1)
        oled.show()

    def show_format_option(self, name, sample):
        oled = self._oled
        if not oled:
            return
        oled.fill(0)
        oled.text("Angle format", 0, 0, 1)
        oled.text(name[:16], 0, 10, 1)
        oled.text(sample, 0, 22, 1)
        oled.text("low=set top=next", 0, 32, 1)
        oled.show()

    def _draw_angle_band(self, angle, fmt, y=12):
        """Render angle text at y without clearing — caller manages fill."""
        oled = self._oled
        if fmt == "2d":
            text = f" {angle:+.2f}" if -10.0 < angle < 10.0 else f"{angle:+.2f}"
            advances = [5 if c == ' ' else 4 if c == '.' else 6 for c in text]
            oled.large_text_adv(text, 0, y, scale=2, advances=advances)
        else:
            if fmt == "1d":
                angle = round(angle, 1)
            else:
                angle = round(angle * 2) / 2
            text = f"{angle:+.1f}"
            if -10.0 < angle < 10.0:
                text = " " + text
            oled.large_text(text, 0, y, scale=2, char_pitch=7)

    def clear(self):
        if self._oled:
            self._oled.fill(0)
            self._oled.show()
