class BatteryService:
    def __init__(self, display_service, button_service):
        self._display = display_service
        self._buttons = button_service

    def read_pct(self):
        """Return battery percentage (0-100), or None when on USB with battery cut."""
        from drivers.battery import read_battery_pct
        return read_battery_pct()

    def show_splash(self):
        import time
        pct = self.read_pct()
        self._show(pct)
        if pct is not None:
            time.sleep_ms(1500)
            return
        # battery cut — keep re-reading; bypass on low button held down
        while True:
            pct = self.read_pct()
            if pct is not None:
                self._show(pct)
                time.sleep_ms(1500)
                return
            if self._buttons.is_pressed('low'):
                return

    def _show(self, pct):
        d = self._display._display  # raw Display instance
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
