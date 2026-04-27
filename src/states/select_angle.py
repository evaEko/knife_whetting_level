import time
from state import State

_CUSTOM = 0


class SelectAngleState(State):
    def __init__(self):
        self._index = 0

    def update(self, device):
        display = device.display
        engine  = device.engine
        buttons = device.buttons
        sensor  = device.sensor
        presets = device.presets

        if presets.empty:
            from states.measure import MeasureState
            return MeasureState()

        n     = len(presets)
        CLEAR = n + 1
        total = n + 2  # Custom + presets + Clear

        if self._index >= total:
            self._index = 0

        display.invert(False)
        self._show(display, self._index, n, CLEAR, presets)

        while True:
            event = buttons.update()

            if event == ('short', 'top'):
                self._index = (self._index + 1) % total
                self._show(display, self._index, n, CLEAR, presets)

            elif event == ('short', 'low'):
                if self._index == _CUSTOM:
                    self._capture_custom(device, display, engine, buttons, sensor)
                elif self._index < CLEAR:
                    name, angle = presets[self._index - 1]
                    engine.set_target(angle)
                    device.settings.target_angle = angle
                    device.settings.save_calibration()
                    print(f"-> PRESET '{name}' {angle}°")
                    display.show_message(f"SET {angle:.0f}", name[:9])
                    time.sleep_ms(1000)
                else:
                    engine.clear_target()
                    device.settings.target_angle = 0.0
                    device.settings.save_calibration()
                    print("-> PRESET cleared")
                    display.show_message("Cleared")
                    time.sleep_ms(1000)
                break

            elif event is not None:
                break

            time.sleep_ms(10)

        from states.measure import MeasureState
        return MeasureState()

    def _show(self, display, index, n, clear, presets):
        if index == _CUSTOM:
            display.show_message("Custom angle", "", "low=set")
        elif index < clear:
            name, angle = presets[index - 1]
            display.show_preset(name, angle)
        else:
            display.show_message("Clear angle", "", "low=clear top=next")

    def _capture_custom(self, device, display, engine, buttons, sensor):
        display.invert(False)
        last_display = 0
        while True:
            raw = sensor.update()
            if raw is not None:
                engine.update(raw)
            now = time.ticks_ms()
            if time.ticks_diff(now, last_display) >= 50:
                last_display = now
                display.show_angle(engine.smooth_angle,
                                   label="low=set",
                                   fmt=engine.angle_format)
            event = buttons.update()
            if event == ('short', 'low'):
                angle = engine.smooth_angle
                engine.set_target(angle)
                device.settings.target_angle = angle
                device.settings.save_calibration()
                print(f"-> CUSTOM {angle:.2f}°")
                display.show_message("SET")
                time.sleep_ms(1000)
                return
            if event is not None:
                return
            time.sleep_ms(10)
