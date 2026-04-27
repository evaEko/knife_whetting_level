import time
from state import State


class CalibrateState(State):
    def __init__(self):
        self._done_at = None

    def enter(self, device):
        display = device.display
        engine = device.engine
        display.invert(False)
        display.show_calibration(engine.smooth_angle, engine.angle_format)

    def update(self, device):
        display = device.display
        engine  = device.engine
        buttons = device.buttons
        sensor  = device.sensor

        if self._done_at is not None:
            if time.ticks_diff(time.ticks_ms(), self._done_at) >= 0:
                from states.measure import MeasureState
                return MeasureState()
            return None

        raw = sensor.update()
        if raw is not None:
            engine.update(raw)
            display.update_angle(engine.smooth_angle, engine.angle_format)

        event = buttons.update()
        if event == ('short', 'low'):
            engine.calibrate()
            device.settings.calibrated_offset = engine.calibrated_offset
            device.settings.save_calibration()
            display.show_angle(0.0, label="SET", fmt=engine.angle_format)
            self._done_at = time.ticks_add(time.ticks_ms(), 500)
            return None
        if event is not None:
            from states.measure import MeasureState
            return MeasureState()

        return None
