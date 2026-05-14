from core.state import State


class InitState(State):
    def enter(self, app):
        app.display.init()
        app.display.show_splash("Blunt")
        app.logging.log("[InitState] enter")
        app.imu.init()
        app.buttons.init()
        app.calibration.load()
        app.battery.show_splash()

    def update(self, app):
        from states.measure_state import MeasureState
        return MeasureState()

    def exit(self, app):
        app.logging.log("[InitState] exit")
