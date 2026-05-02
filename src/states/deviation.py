import time
from state import State

_STEP = 0.1
_MIN  = 0.0
_MAX  = 4.0


class DeviationState(State):

    def enter(self, device):
        self._value   = round(device.engine.deviation_threshold, 1)
        self._done_at = None
        device.display.invert(False)
        device.display.show_deviation(self._value)

    def update(self, device):
        if self._done_at is not None:
            if time.ticks_diff(time.ticks_ms(), self._done_at) >= 0:
                from states.measure import MeasureState
                return MeasureState()
            return None

        event = device.buttons.update()

        if event == ('short', 'top'):
            self._value = round(min(_MAX, self._value + _STEP), 1)
            device.display.show_deviation(self._value)

        elif event == ('short', 'low'):
            self._value = round(max(_MIN, self._value - _STEP), 1)
            device.display.show_deviation(self._value)

        elif event == ('long', 'low'):
            device.engine.deviation_threshold = self._value
            from drivers.config_rw import write_config
            write_config('DEVIATION_THRESHOLD', f"{self._value:.1f}")
            device.display.show_message("Saved!", f"{self._value:.1f} deg")
            self._done_at = time.ticks_add(time.ticks_ms(), 800)

        elif event is not None:
            from states.measure import MeasureState
            return MeasureState()

        return None
