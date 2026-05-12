from core.state import State


class BleToggleState(State):
    def enter(self, app):
        self._render(app)
        app.logging.log("[BleToggleState] enter")

    def update(self, app):
        app.ble.poll()
        self._render(app)
        if app.button_event == 'short_top':
            app.ble.toggle()
            app.logging.log(
                "[BleToggleState] BLE " + ("on" if app.ble.enabled else "off")
            )
            self._render(app)
        elif app.button_event == 'short_low':
            from states.settings_state import SettingsState
            return SettingsState(app.settings_items)
        return None

    def exit(self, app):
        app.logging.log("[BleToggleState] exit")

    def _render(self, app):
        app.display.show_ble_status(app.ble.connected, app.ble.enabled)
