import math
import time
from core.setting_handler import SettingHandler

_N_SAMPLES = 20
_SETTLE_MS = 50


class SurfaceLevelHandler(SettingHandler):
    def __init__(self, storage_key, prompt, saved_msg, on_save):
        self._storage_key = storage_key
        self._prompt      = prompt
        self._saved_msg   = saved_msg
        self._on_save     = on_save

    def enter(self, app):
        app.display.show_text(*self._prompt)
        app.logging.log("[SurfaceLevelHandler] enter key=" + self._storage_key)

    def update(self, app):
        if app.button_event == 'short_top':
            return 'measure'
        if app.button_event == 'short_low':
            vec = self._capture(app)
            self._on_save(vec)
            app.logging.log("[SurfaceLevelHandler] " + self._storage_key + "=" + self._fmt(vec))
            app.display.show_text(self._saved_msg, self._fmt(vec))
            time.sleep_ms(2000)
            return 'measure'
        return None

    def exit(self, app):
        app.logging.log("[SurfaceLevelHandler] exit key=" + self._storage_key)

    def _capture(self, app):
        delay_ms = int(getattr(app.config, 'capture_delay_sec', 5)) * 1000
        app.display.show_text("Hold still...")
        time.sleep_ms(delay_ms)
        app.display.show_text("Capturing...")
        sx, sy, sz = 0.0, 0.0, 0.0
        count = 0
        while count < _N_SAMPLES:
            if app.imu.update():
                gx, gy, gz = app.imu.get_gravity()
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
