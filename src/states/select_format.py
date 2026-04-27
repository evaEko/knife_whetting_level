import time
import machine
from state import State

_OPTIONS = [
    ("2 decimals", "2d",     "+12.34"),
    ("1 decimal",  "1d",     "+12.3"),
    ("0/5 steps",  "1d_half", "+12.5"),
]


class SelectAngleFormatState(State):
    def __init__(self):
        self._index = 0

    def update(self, device):
        display = device.display
        engine  = device.engine
        buttons = device.buttons

        for i, (_, key, _) in enumerate(_OPTIONS):
            if key == engine.angle_format:
                self._index = i
                break

        display.invert(False)
        name, _, sample = _OPTIONS[self._index]
        display.show_format_option(name, sample)

        while True:
            event = buttons.update()

            if event == ('short', 'top'):
                self._index = (self._index + 1) % len(_OPTIONS)
                name, _, sample = _OPTIONS[self._index]
                display.show_format_option(name, sample)

            elif event == ('short', 'low'):
                name, key, _ = _OPTIONS[self._index]
                if key != engine.angle_format:
                    engine.angle_format = key
                    device.settings.angle_format = key
                    device.settings.save_angle_format()
                    display.show_message("FORMAT SET", name[:16], "Rebooting...")
                    time.sleep_ms(120)
                    machine.reset()
                else:
                    display.show_message("No change")
                    time.sleep_ms(500)
                break

            elif event is not None:
                break

            time.sleep_ms(10)

        from states.measure import MeasureState
        return MeasureState()
