import time
from core.state import State
from core.container import Container


class ClearTargetState(State):
    def enter(self):
        Container.calibration_service.clear_target()
        Container.display_service.show_text("Target", "cleared")
        time.sleep_ms(1500)

    def update(self):
        from states.measure_state import MeasureState
        return MeasureState()

    def exit(self):
        pass
