class BatteryService:
    def __init__(self, display_service, button_service):
        self._display  = display_service
        self._buttons  = button_service
        self._bypassed = False

    def read_pct(self):
        """Return battery percentage (0-100), or None when on USB with battery cut."""
        from drivers.battery import read_battery_pct
        return read_battery_pct()

    def on_usb(self):
        """True if USB VBUS is present (charging or connected for flashing)."""
        from drivers.battery import usb_connected
        return usb_connected()

    def check_usb(self):
        """Call periodically during operation. Shows the charging splash if
        USB is connected, unless the user already bypassed it for this USB
        session (the bypass clears once unplugged). Returns True if the
        splash was shown (caller may want to discard a stale button event)."""
        if not self.on_usb():
            self._bypassed = False
            return False
        if self._bypassed:
            return False
        self.show_splash()
        return True

    def show_splash(self):
        """Show battery/charging status. While on USB, stay here (refreshing
        the screen) instead of entering operating mode — unplugging falls
        straight through to measuring. Hold 'low' to bypass either way; a
        bypass also suppresses check_usb() re-prompts until unplugged."""
        import time
        self._render()
        if not self.on_usb():
            self._bypassed = False
            time.sleep_ms(1500)
            return
        while self.on_usb():
            if self._buttons.is_pressed('low'):
                self._bypassed = True
                return
            time.sleep_ms(500)
            self._render()
        self._bypassed = False

    def _render(self):
        self._display.show_battery(self.read_pct(), charging=self.on_usb())
