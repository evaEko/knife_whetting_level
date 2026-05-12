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
        if pct is None:
            self._display.show_text("Not charging!", "Battery cut", "Low: continue")
            while True:
                if self._buttons.update() == 'short_low':
                    break
        else:
            self._display.show_text("Battery", "{}%".format(pct))
            time.sleep_ms(1500)
