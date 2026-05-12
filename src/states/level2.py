import time
import math
import machine
from state import State

_SETTLE_MS = 1000
_SAMPLE_MS = 500
_SAMPLE_N  = 20


class Level2State(State):
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
        device.display.show_message("Blade edge", "on stone,", "low=press")

    def update(self, device):
        buttons  = device.buttons
        sensor   = device.sensor
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
                    settings.edge_normal = None
                    settings.save()
                    sensor.clear_edge_normal()
                    display.show_reboot_confirm("Blade rst", "RESET")
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
                self._finish(device)

        return None

    def _finish(self, device):
        settings = device.settings
        sensor   = device.sensor
        display  = device.display

        if settings.surface_normal is None:
            display.show_message("Do board", "level first", "top=back")
            self._done_at = time.ticks_add(time.ticks_ms(), 2000)
            self._phase   = 'feedback'
            return

        gx = self._gx_sum / self._sample_count
        gy = self._gy_sum / self._sample_count
        gz = self._gz_sum / self._sample_count
        nx, ny, nz = settings.surface_normal

        # Edge direction = cross(surface_normal, g_step2)
        # — perpendicular to both the stone normal and the lifted gravity vector,
        #   which is the axis the blade rotated around (the knife edge).
        ex = ny*gz - nz*gy
        ey = nz*gx - nx*gz
        ez = nx*gy - ny*gx
        mag = math.sqrt(ex*ex + ey*ey + ez*ez)
        if mag < 0.05:
            # Vectors nearly parallel — blade wasn't lifted enough
            display.show_message("Lift more", "blade too", "flat")
            self._done_at = time.ticks_add(time.ticks_ms(), 2000)
            self._phase   = 'feedback'
            return

        ex, ey, ez = ex/mag, ey/mag, ez/mag
        settings.edge_normal = (ex, ey, ez)
        settings.save()
        sensor.set_edge_normal(ex, ey, ez)
        display.show_reboot_confirm("Saved!", "DONE")
        self._done_at = time.ticks_add(time.ticks_ms(), 800)
        self._phase   = 'feedback'
