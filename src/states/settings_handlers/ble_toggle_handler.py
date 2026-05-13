from core.setting_handler import SettingHandler


class BleToggleHandler(SettingHandler):
    def enter(self, app):
        self._render(app)
        app.logging.log("[BleToggleHandler] enter")

    def update(self, app):
        app.ble.poll()
        self._render(app)
        if app.button_event == 'short_top':
            app.ble.toggle()
            app.logging.log("[BleToggleHandler] BLE " + ("on" if app.ble.enabled else "off"))
            self._render(app)
        elif app.button_event == 'short_low':
            return 'settings'
        return None

    def exit(self, app):
        app.logging.log("[BleToggleHandler] exit")

    def _render(self, app):
        app.display.show_ble_status(app.ble.connected, app.ble.enabled)
