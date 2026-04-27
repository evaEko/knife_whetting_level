import time
from state import State

_DISPLAY_INTERVAL = 50


class MeasureState(State):
    def __init__(self):
        self._last_display = 0

    def update(self, device):
        raw = device.sensor.update()
        if raw is not None:
            device.engine.update(raw)

        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_display) >= _DISPLAY_INTERVAL:
            self._last_display = now
            device.display.invert(not device.engine.on_target)
            device.display.show_angle(device.engine.smooth_angle,
                                      fmt=device.engine.angle_format)

        event = device.buttons.update()
        if event == ('short', 'low'):
            from states.calibrate import CalibrateState
            return CalibrateState()
        if event == ('short', 'top'):
            from states.select_angle import SelectAngleState
            return SelectAngleState()
        if event == ('long', 'top'):
            from states.select_format import SelectAngleFormatState
            return SelectAngleFormatState()
        if event == ('short', 'both'):
            from states.flash import FlashState
            return FlashState()
        if event == ('long', 'low'):
            from states.level import LevelState
            return LevelState()
        return None
