import time
from core.state import State


class SetPresetState(State):
    def __init__(self, angle):
        self._angle = angle

    def enter(self, app):
        app.calibration.set_target_angle(self._angle)
        app.display.show_splash("{:.1f}".format(self._angle))
        time.sleep_ms(1500)

    def update(self, app):
        from states.measure_state import MeasureState
        return MeasureState()

    def exit(self, app):
        pass
