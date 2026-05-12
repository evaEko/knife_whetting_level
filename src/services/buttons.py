from machine import Pin
from utime import ticks_ms, ticks_diff

_LONG_PRESS_MS = 800
_DEBOUNCE_MS   = 30


class ButtonService:
    def __init__(self, pin_low, pin_top):
        self._pin_low = pin_low
        self._pin_top = pin_top
        self._low     = None
        self._top     = None
        self._start   = [None, None]  # press start time per button

    def init(self):
        self._low = Pin(self._pin_low, Pin.IN, Pin.PULL_UP)
        self._top = Pin(self._pin_top, Pin.IN, Pin.PULL_UP)

    def is_pressed(self, button='low'):
        pin = self._low if button == 'low' else self._top
        return pin.value() == 0

    def update(self):
        """Call once per loop tick. Returns event string or None.

        Events: 'both', 'short_low', 'long_low', 'short_top', 'long_top'
        Events fire on release (except 'both' which fires while held).
        """
        if self._low.value() == 0 and self._top.value() == 0:
            return 'both'

        pins   = [self._low, self._top]
        names  = ['low', 'top']
        for i, (pin, name) in enumerate(zip(pins, names)):
            pressed = pin.value() == 0
            if pressed and self._start[i] is None:
                self._start[i] = ticks_ms()
            elif not pressed and self._start[i] is not None:
                duration = ticks_diff(ticks_ms(), self._start[i])
                self._start[i] = None
                if duration < _DEBOUNCE_MS:
                    continue
                kind = 'long' if duration >= _LONG_PRESS_MS else 'short'
                return kind + '_' + name
        return None
