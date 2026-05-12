from core.state import State
from core.container import Container


class InitState(State):
    def enter(self):
        Container.display_service.init()
        Container.display_service.show_text("Init...")
        Container.logging_service.log("[InitState] enter")

        Container.imu_service.init()
        Container.button_service.init()

    def update(self):
        from states.measure_state import MeasureState
        return MeasureState()

    def exit(self):
        Container.display_service.show_text("Init OK")
        Container.logging_service.log("[InitState] exit")
