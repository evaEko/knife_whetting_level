import math
import time
from core.state import State
from core.container import Container

_N_SAMPLES   = 20
_SETTLE_MS   = 50    # delay between samples


class SurfaceLevelState(State):
    def __init__(self, storage_key, prompt, saved_msg, on_save=None):
        self._storage_key = storage_key
        self._prompt      = prompt
        self._saved_msg   = saved_msg
        self._on_save     = on_save

    def enter(self):
        Container.display_service.show_text(*self._prompt)
        Container.logging_service.log("[SurfaceLevelState] enter key=" + self._storage_key)

    def update(self):
        if Container.button_event == 'short_top':
            from states.measure_state import MeasureState
            return MeasureState()
        if Container.button_event == 'short_low':
            vec = self._capture()
            if self._on_save is not None:
                self._on_save(vec)
            else:
                Container.storage_service.set(self._storage_key, self._fmt(vec))
            Container.logging_service.log("[SurfaceLevelState] " + self._storage_key + "=" + self._fmt(vec))
            Container.display_service.show_text(self._saved_msg, self._fmt(vec))
            time.sleep_ms(2000)
            from states.measure_state import MeasureState
            return MeasureState()
        return None

    def _capture(self):
        delay_ms = int(getattr(Container.config_service, 'capture_delay_sec', 5)) * 1000
        Container.display_service.show_text("Hold still...")
        time.sleep_ms(delay_ms)
        Container.display_service.show_text("Capturing...")
        sx, sy, sz = 0.0, 0.0, 0.0
        count = 0
        while count < _N_SAMPLES:
            if Container.imu_service.update():
                gx, gy, gz = Container.imu_service.get_gravity()
                sx += gx
                sy += gy
                sz += gz
                count += 1
            time.sleep_ms(_SETTLE_MS)
        mx, my, mz = sx / _N_SAMPLES, sy / _N_SAMPLES, sz / _N_SAMPLES
        length = math.sqrt(mx*mx + my*my + mz*mz)
        return (mx / length, my / length, mz / length)

    def _fmt(self, v):
        return "{:.3f},{:.3f},{:.3f}".format(v[0], v[1], v[2])

    def exit(self):
        Container.logging_service.log("[SurfaceLevelState] exit key=" + self._storage_key)
