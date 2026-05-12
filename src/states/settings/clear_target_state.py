import time
from core.state import State
from core.container import Container


class ClearTargetState(State):
    def enter(self):
        Container.calibration_service.clear_target()
        Container.display_service.show_splash("Cleared")
        time.sleep_ms(1500)

    def update(self):
        from states.measure_state import MeasureState
        return MeasureState()

    def exit(self):
        pass
