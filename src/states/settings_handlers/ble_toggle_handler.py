from core.setting_handler import SettingHandler
from services.logging import log


class BleToggleHandler(SettingHandler):
    def enter(self, app):
        self._was_connected = app.ble.connected
        self._render(app)
        log("[BleToggleHandler] enter")

    def update(self, app):
        app.ble.poll()
        now_connected = app.ble.connected
        if now_connected and not self._was_connected:
            return 'measure'
        self._was_connected = now_connected
        self._render(app)
        if app.button_event == 'short_top':
            app.ble.toggle()
            app.config.set('ble_enabled', 1 if app.ble.enabled else 0)
            log("[BleToggleHandler] BLE " + ("on" if app.ble.enabled else "off"))
            self._render(app)
        elif app.button_event == 'short_low':
            return 'settings'
        return None

    def exit(self, app):
        log("[BleToggleHandler] exit")

    def _render(self, app):
        app.display.show_ble_status(app.ble.connected, app.ble.enabled)
