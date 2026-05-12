from core.state import State
from core.container import Container


class BleToggleState(State):
    def enter(self):
        self._render()
        Container.logging_service.log("[BleToggleState] enter")

    def _render(self):
        ble = Container.ble_service
        if ble.connected:
            status = "connected"
        elif ble.enabled:
            status = "connecting"
        else:
            status = "Off"
        d = Container.display_service._display
        d.fill(0)
        scale = 1
        w = ((len(status) - 1) * 7 + 8) * scale
        x = max(0, (d.width - w) // 2)
        y = max(0, (d.height - 8 * scale) // 2 - 4)
        d.large_text(status, x, y, scale=scale, char_pitch=7)
        d.text("top:tgl  low:back", 0, 32, 1)
        d.show()

    def update(self):
        Container.ble_service.poll()  # drain IRQ queue so connected state stays fresh
        self._render()
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
