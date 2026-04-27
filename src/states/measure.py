import time
from state import State
from config import SHOW_PRESET_NAME, SHOW_TARGET_ANGLE

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
            engine = device.engine
            device.display.invert(not engine.on_target)
            has_target = engine.target_angle != 0.0
            target = engine.target_angle if (has_target and SHOW_TARGET_ANGLE) else None
            name   = engine.target_name  if (has_target and SHOW_PRESET_NAME)  else None
            device.display.show_measure(engine.smooth_angle,
                                        fmt=engine.angle_format,
                                        target=target,
                                        name=name)

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
