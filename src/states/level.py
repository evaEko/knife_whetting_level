import time
import machine
from state import State


class LevelState(State):
    def update(self, device):
        display = device.display
        sensor  = device.sensor
        buttons = device.buttons
        engine  = device.engine
        settings = device.settings

        display.invert(False)
        display.show_message("Place on", "straight", "surface")

        buttons.wait_release('low')
        time.sleep_ms(50)

        while True:
            raw = sensor.update()
            if raw is not None:
                engine.raw_angle = raw

            if buttons.is_pressed('low'):
                time.sleep_ms(50)
                if buttons.is_pressed('low'):
                    start = time.ticks_ms()
                    while buttons.is_pressed('low'):
                        time.sleep_ms(10)
                    duration = time.ticks_diff(time.ticks_ms(), start)

                    if duration >= 800:
                        settings.reset_board_offset()
                        settings.reset_calibration()
                        engine.board_offset      = 0.0
                        engine.calibrated_offset = 0.0
                        engine.smooth_angle      = 0.0
                        display.show_message("BL reset", "", "Rebooting...")
                    else:
                        settings.save_board_offset(engine.raw_angle)
                        settings.reset_calibration()
                        engine.board_offset      = engine.raw_angle
                        engine.calibrated_offset = 0.0
                        engine.smooth_angle      = 0.0
                        display.show_message("Saved!", "", "Rebooting...")

                    time.sleep_ms(800)
                    machine.reset()

            time.sleep_ms(10)
