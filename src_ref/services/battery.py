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
        if pct is None:
            self._display.show_text("Not charging!", "Battery cut", "Low: bypass")
        else:
            self._display.show_text("Battery", "{}%".format(pct))
