import time
import machine
from state import State
from states.ble_toggle import read_ble_enabled, write_ble_enabled

_OPTIONS = [
    "Calib",
    "Level",
    "Bluetooth",
    "Exit",
]


class SettingsMenuState(State):
    _index = 0  # class-level: persists across visits

    def __init__(self):
        self._last_draw = 0

    def enter(self, device):
        device.display.invert(False)
        self._draw(device)

    def update(self, device):
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_draw) >= 200:
            self._last_draw = now
            if _OPTIONS[SettingsMenuState._index] == "Bluetooth":
                self._draw(device)

        event = device.buttons.update()
        if event == ('short', 'top'):
            SettingsMenuState._index = (SettingsMenuState._index + 1) % len(_OPTIONS)
            self._draw(device)
            return None

        if event == ('short', 'low'):
            choice = _OPTIONS[SettingsMenuState._index]
            if choice == "Calib":
                from states.calibrate import CalibrateState
                return CalibrateState()
            if choice == "Level":
                from states.level import LevelState
                return LevelState()
            if choice == "Bluetooth":
                enabled = not read_ble_enabled()
                write_ble_enabled(enabled)
                title = "BL ON" if enabled else "BL OFF"
                device.display.show_reboot_confirm(title, "BLE")
                time.sleep_ms(1000)
                machine.reset()
            from states.measure import MeasureState
            return MeasureState()

        if event is not None:
            from states.measure import MeasureState
            return MeasureState()

        return None

    def _draw(self, device):
        choice = _OPTIONS[SettingsMenuState._index]
        if choice == "Bluetooth":
            try:
                from states.ble_toggle import read_ble_enabled
                enabled = read_ble_enabled()
                status = "On" if enabled else "Off"
            except Exception:
                enabled = False
                status = "?"
            hint = "low=off" if enabled else "low=on"
            device.display.show_settings_item("BL:" + status, hint=hint)
        else:
            device.display.show_settings_item(choice)
