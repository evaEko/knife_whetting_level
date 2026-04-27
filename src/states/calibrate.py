import time
from state import State


class CalibrateState(State):
    def update(self, device):
        display = device.display
        engine  = device.engine
        buttons = device.buttons
        sensor  = device.sensor

        display.invert(False)
        display.show_calibration(engine.smooth_angle, engine.angle_format)

        while True:
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
                time.sleep_ms(500)
                break
            if event is not None:
                break
            time.sleep_ms(10)

        from states.measure import MeasureState
        return MeasureState()
