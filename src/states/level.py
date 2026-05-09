import time
import math
import machine
from state import State

_SETTLE_MS = 1000
_SAMPLE_MS = 500
_SAMPLE_N  = 20


class LevelState(State):
    def __init__(self):
        self._phase        = 'wait_release'
        self._press_start  = None
        self._done_at      = None
        self._gx_sum       = 0.0
        self._gy_sum       = 0.0
        self._gz_sum       = 0.0
        self._sample_count = 0
        self._sample_end   = None

    def enter(self, device):
        device.display.invert(False)
        device.display.show_message("Place flat", "low=press")

    def update(self, device):
        buttons  = device.buttons
        sensor   = device.sensor
        engine   = device.engine
        settings = device.settings
        display  = device.display

        if self._phase == 'wait_release':
            if not buttons.is_pressed('low'):
                self._phase = 'prompt_a'
            return None

        if self._phase == 'feedback':
            if time.ticks_diff(time.ticks_ms(), self._done_at) >= 0:
                machine.reset()
            return None

        sensor.update()

        if self._phase == 'prompt_a':
            if buttons.is_pressed('low'):
                self._press_start = time.ticks_ms()
                self._phase = 'timing_a'

        elif self._phase == 'timing_a':
            if not buttons.is_pressed('low'):
                duration = time.ticks_diff(time.ticks_ms(), self._press_start)
                if duration >= 800:
                    settings.reset_board_offset()
                    settings.reset_calibration()
                    sensor.clear_surface_normal()
                    engine.board_offset      = 0.0
                    engine.calibrated_offset = 0.0
                    engine.smooth_angle      = 0.0
                    display.show_reboot_confirm("BL reset", "RESET")
                    self._done_at = time.ticks_add(time.ticks_ms(), 800)
                    self._phase   = 'feedback'
                else:
                    self._done_at = time.ticks_add(time.ticks_ms(), _SETTLE_MS)
                    self._phase   = 'settling'

        elif self._phase == 'settling':
            if time.ticks_diff(time.ticks_ms(), self._done_at) >= 0:
                self._gx_sum       = 0.0
                self._gy_sum       = 0.0
                self._gz_sum       = 0.0
                self._sample_count = 0
                self._sample_end   = time.ticks_add(time.ticks_ms(), _SAMPLE_MS)
                self._phase        = 'sampling'

        elif self._phase == 'sampling':
            g = sensor.get_gravity()
            if g is not None:
                gx, gy, gz = g
                self._gx_sum       += gx
                self._gy_sum       += gy
                self._gz_sum       += gz
                self._sample_count += 1
            done = (time.ticks_diff(time.ticks_ms(), self._sample_end) >= 0
                    or self._sample_count >= _SAMPLE_N)
            if done and self._sample_count > 0:
                mx = self._gx_sum / self._sample_count
                my = self._gy_sum / self._sample_count
                mz = self._gz_sum / self._sample_count
                mag = math.sqrt(mx*mx + my*my + mz*mz)
                nx, ny, nz = (mx/mag, my/mag, mz/mag) if mag > 0.0 else (0.0, 0.0, 1.0)
                settings.surface_normal    = (nx, ny, nz)
                settings.board_offset      = 0.0
                settings.calibrated_offset = 0.0
                settings.target_angle      = 0.0
                settings.save()
                sensor.set_surface_normal(nx, ny, nz)
                engine.board_offset      = 0.0
                engine.calibrated_offset = 0.0
                engine.smooth_angle      = 0.0
                display.show_reboot_confirm("Saved!", "DONE")
                self._done_at = time.ticks_add(time.ticks_ms(), 800)
                self._phase   = 'feedback'

        return None
