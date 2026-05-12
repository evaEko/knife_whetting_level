import time
from core.state import State
from core.container import Container


class SetPresetState(State):
    def __init__(self, angle):
        self._angle = angle

    def enter(self):
        Container.calibration_service.set_target_angle(self._angle)
        Container.display_service.show_text("Target set", "{:.1f}".format(self._angle))
        time.sleep_ms(1500)

    def update(self):
        from states.measure_state import MeasureState
        return MeasureState()

    def exit(self):
        pass
