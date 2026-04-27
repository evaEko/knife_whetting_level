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
            oled.text("To charge", 0, 0, 1)
            oled.large_text("PLUG", 8, 12, scale=2, char_pitch=7)
            oled.text("low=pass", 0, 32, 1)
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

    def show_measure(self, angle, fmt="1d_half", target=None, name=None, ble_on=False):
        """Measuring screen: optional name top, big angle middle, target bottom."""
        oled = self._oled
        if not oled:
            return
        oled.fill(0)
        if name:
            oled.text(name[:9], 0, 0, 1)
        self._draw_angle_band(angle, fmt, y=12)
        if target is not None:
            oled.text(self._fmt_target(target, fmt), 0, 32, 1)
        if ble_on:
            self._draw_ble_star(oled)
        oled.show()

    def show_flash(self):
        oled = self._oled
        if not oled:
            return
        oled.fill(0)
        oled.text("Ready to", 0, 2, 1)
        oled.large_text("FLASH", 1, 20, scale=2, char_pitch=7)
        oled.show()

    @staticmethod
    def _fmt_target(angle, fmt):
        if fmt == "2d":
            return f"> {angle:+.2f}"
        if fmt == "1d":
            angle = round(angle, 1)
        else:
            angle = round(angle * 2) / 2
        return f"> {angle:.1f}"

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

    def show_set_confirmation(self, angle, fmt="1d_half", name=None):
        """Confirmation after preset selection: Setting / big angle / name."""
        oled = self._oled
        if not oled:
            return
        oled.fill(0)
        oled.text("Setting", 0, 0, 1)
        self._draw_angle_band(angle, fmt, y=12)
        if name:
            oled.text(name[:9], 0, 32, 1)
        oled.show()

    def show_custom(self):
        oled = self._oled
        if not oled:
            return
        oled.fill(0)
        oled.text("Custom", 0, 0, 1)
        oled.large_text("angle", 1, 12, scale=2, char_pitch=7)
        oled.text("low=set", 0, 32, 1)
        oled.show()

    def show_cleared(self):
        oled = self._oled
        if not oled:
            return
        oled.fill(0)
        oled.text("Preset", 0, 0, 1)
        oled.large_text("CLEAR", 1, 12, scale=2, char_pitch=7)
        oled.text("Cleared!", 0, 32, 1)
        oled.show()

    def show_reboot_confirm(self, title, action):
        """Confirmation before reboot: title small top, action big middle, Rebooting bottom."""
        oled = self._oled
        if not oled:
            return
        oled.fill(0)
        oled.text(title, 0, 0, 1)
        oled.large_text(action, 1, 12, scale=2, char_pitch=7)
        oled.text("Rebooting", 0, 32, 1)
        oled.show()

    def show_level_prompt(self):
        oled = self._oled
        if not oled:
            return
        oled.fill(0)
        oled.text("Place on", 0, 0, 1)
        oled.large_text("LEVEL", 1, 12, scale=2, char_pitch=7)
        oled.text("surface", 0, 32, 1)
        oled.show()

    def show_clear(self, current_angle, fmt="1d_half"):
        """Clear preset item: current target top, CLEAR big middle, hint bottom."""
        oled = self._oled
        if not oled:
            return
        oled.fill(0)
        oled.text(self._fmt_target(current_angle, fmt), 0, 0, 1)
        oled.large_text("CLEAR", 1, 12, scale=2, char_pitch=7)
        oled.text("low=clear", 0, 32, 1)
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

    def show_settings_item(self, name, hint="low=select"):
        """Settings menu item: big label + single action hint."""
        oled = self._oled
        if not oled:
            return
        oled.fill(0)
        text = name[:9]
        if text.startswith("BL:"):
            pitch = 7 if len(text) <= 5 else 5
            oled.large_text(text, 0, 12, scale=2, char_pitch=pitch)
        elif len(text) <= 5:
            oled.large_text(text, 1, 12, scale=2, char_pitch=7)
        else:
            oled.large_text(text, 1, 12, scale=2, char_pitch=4)
        oled.text(hint, 0, 32, 1)
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

    @staticmethod
    def _draw_ble_star(oled):
        """Draw a tiny BLE indicator in the lower-right corner."""
        x = 68
        y = 35
        fb = oled.fb
        fb.pixel(x, y, 1)
        fb.pixel(x, y - 3, 1)
        fb.pixel(x, y + 3, 1)
        fb.pixel(x - 3, y, 1)
        fb.pixel(x + 3, y, 1)
        fb.pixel(x, y - 1, 1)
        fb.pixel(x, y + 1, 1)
        fb.pixel(x - 1, y, 1)
        fb.pixel(x + 1, y, 1)
        fb.pixel(x - 2, y - 2, 1)
        fb.pixel(x + 2, y + 2, 1)
        fb.pixel(x - 2, y + 2, 1)
        fb.pixel(x + 2, y - 2, 1)

    def clear(self):
        if self._oled:
            self._oled.fill(0)
            self._oled.show()
