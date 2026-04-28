import time
from state import State
from config import SHOW_PRESET_NAME, SHOW_TARGET_ANGLE, DISPLAY_INTERVAL_MS


class MeasureState(State):
    def __init__(self):
        self._last_display = 0

    def enter(self, device):
        if device.ble is not None and device.ble.connected:
            device.ble.send_target_state(device)

    def update(self, device):
        raw = device.sensor.update()
        if raw is not None:
            device.engine.update(raw)

        if device.ble is not None:
            device.ble.tick(device)

        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_display) >= DISPLAY_INTERVAL_MS:
            self._last_display = now
            engine = device.engine
            device.display.invert(not engine.on_target)
            has_target = engine.target_angle != 0.0
            target = engine.target_angle if (has_target and SHOW_TARGET_ANGLE) else None
            name   = engine.target_name  if (has_target and SHOW_PRESET_NAME)  else None
            device.display.show_measure(engine.smooth_angle,
                                        fmt=engine.angle_format,
                                        target=target,
                                        name=name,
                                        ble_on=(device.ble is not None))

        event = device.buttons.update()
        if event == ('short', 'low'):
            from states.settings_menu import SettingsMenuState
            return SettingsMenuState()
        if event == ('short', 'top'):
            from states.select_angle import SelectAngleState
            return SelectAngleState()
        if event == ('long', 'top'):
            from states.select_format import SelectAngleFormatState
            return SelectAngleFormatState()
        if event == ('short', 'both'):
            from states.flash import FlashState
            return FlashState()
        return None
