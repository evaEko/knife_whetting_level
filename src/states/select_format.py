import time
import machine
from state import State

_OPTIONS = [
    ("2 decimals", "2d",      "+12.34"),
    ("1 decimal",  "1d",      "+12.3"),
    ("0/5 steps",  "1d_half", "+12.5"),
]


class SelectAngleFormatState(State):
    _index = 0  # class-level: persists across visits

    def __init__(self):
        self._done_at = None
        self._reboot  = False

    def enter(self, device):
        for i, (_, key, _) in enumerate(_OPTIONS):
            if key == device.engine.angle_format:
                SelectAngleFormatState._index = i
                break
        device.display.invert(False)
        name, _, sample = _OPTIONS[SelectAngleFormatState._index]
        device.display.show_format_option(name, sample)

    def update(self, device):
        display = device.display
        engine  = device.engine
        buttons = device.buttons

        if self._done_at is not None:
            if time.ticks_diff(time.ticks_ms(), self._done_at) >= 0:
                if self._reboot:
                    machine.reset()
                from states.measure import MeasureState
                return MeasureState()
            return None

        event = buttons.update()
        if event == ('short', 'top'):
            SelectAngleFormatState._index = (SelectAngleFormatState._index + 1) % len(_OPTIONS)
            name, _, sample = _OPTIONS[SelectAngleFormatState._index]
            display.show_format_option(name, sample)

        elif event == ('short', 'low'):
            name, key, _ = _OPTIONS[SelectAngleFormatState._index]
            if key != engine.angle_format:
                engine.angle_format = key
                device.settings.angle_format = key
                device.settings.save()
                display.show_reboot_confirm(name[:9], "FORMAT")
                self._reboot  = True
                self._done_at = time.ticks_add(time.ticks_ms(), 120)
            else:
                display.show_message("No change")
                self._done_at = time.ticks_add(time.ticks_ms(), 500)

        elif event is not None:
            from states.measure import MeasureState
            return MeasureState()

        return None
