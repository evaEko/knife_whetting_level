import time
from config import BTN_LOW, BTN_TOP, LONG_PRESS_MS
from drivers.button import Button


class Buttons:
    def __init__(self):
        self.low  = None
        self.top  = None
        self._both_start = None

    def init(self):
        try:
            self.low = Button(BTN_LOW)
            self.top = Button(BTN_TOP)
            print("BTN OK")
        except Exception as e:
            print(f"BTN ERROR: {e}")

    @property
    def ready(self):
        return self.low is not None and self.top is not None

    def update(self):
        """Return the next input event as (kind, source) or None.

        kind:   'short' | 'long'
        source: 'low'   | 'top' | 'both'
        """
        both = (self.low and self.low.is_pressed() and
                self.top and self.top.is_pressed())

        if both:
            if self._both_start is None:
                self._both_start = time.ticks_ms()
            return None  # consume individual events while both held

        if self._both_start is not None:
            duration = time.ticks_diff(time.ticks_ms(), self._both_start)
            self._both_start = None
            # drain pending individual events so they don't fire after release
            if self.low: self.low.update()
            if self.top: self.top.update()
            if duration < LONG_PRESS_MS:
                return ('short', 'both')
            return None

        ev_low = self.low.update() if self.low else None
        ev_top = self.top.update() if self.top else None

        if ev_low: return (ev_low, 'low')
        if ev_top: return (ev_top, 'top')
        return None

    def is_pressed(self, which='low'):
        btn = self.low if which == 'low' else self.top
        return btn.is_pressed() if btn else False

    def wait_release(self, which='low'):
        while self.is_pressed(which):
            time.sleep_ms(10)
