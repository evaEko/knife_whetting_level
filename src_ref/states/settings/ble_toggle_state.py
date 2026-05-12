from core.state import State
from core.container import Container


class BleToggleState(State):
    def enter(self):
        self._render()
        Container.logging_service.log("[BleToggleState] enter")

    def _render(self):
        ble = Container.ble_service
        status = "On" if ble.enabled else "Off"
        conn   = "connected" if ble.connected else "advertising" if ble.enabled else ""
        Container.display_service.show_text(
            "Bluetooth",
            status,
            conn,
            "top: toggle",
            "low: back",
        )

    def update(self):
        if Container.button_event == 'short_top':
            Container.ble_service.toggle()
            Container.logging_service.log(
                "[BleToggleState] BLE " + ("on" if Container.ble_service.enabled else "off")
            )
            self._render()
        elif Container.button_event == 'short_low':
            from states.settings_state import SettingsState
            return SettingsState(Container.settings_items)
        return None

    def exit(self):
        Container.logging_service.log("[BleToggleState] exit")
