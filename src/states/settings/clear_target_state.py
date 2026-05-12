import time
from core.state import State


class ClearTargetState(State):
    def enter(self, app):
        app.calibration.clear_target()
        app.display.show_splash("Cleared")
        time.sleep_ms(1500)

    def update(self, app):
        from states.measure_state import MeasureState
        return MeasureState()

    def exit(self, app):
        pass
