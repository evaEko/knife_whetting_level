import time
import math
import machine
from state import State

_SETTLE_MS = 1000
_SAMPLE_MS = 500
_SAMPLE_N  = 20


class LevelState(State):
    def __init__(self):
        self._phase       = 'wait_release'  # wait_release | measuring | timing | settling | sampling | feedback
        self._press_start = None
        self._done_at     = None
        self._action      = None  # 'save' | 'reset'
        self._samples     = []
        self._sample_end  = None

    def enter(self, device):
        device.display.invert(False)
        device.display.show_level_prompt()

    def update(self, device):
        buttons  = device.buttons
        sensor   = device.sensor
        engine   = device.engine
        settings = device.settings
        display  = device.display

        if self._phase == 'wait_release':
            if not buttons.is_pressed('low'):
                self._phase = 'measuring'
            return None

        if self._phase == 'feedback':
            if time.ticks_diff(time.ticks_ms(), self._done_at) >= 0:
                machine.reset()
            return None

        raw = sensor.update()
        if raw is not None:
            engine.raw_angle = raw

        if self._phase == 'measuring':
            if buttons.is_pressed('low'):
                self._press_start = time.ticks_ms()
                self._phase = 'timing'

        elif self._phase == 'timing':
            if not buttons.is_pressed('low'):
                duration = time.ticks_diff(time.ticks_ms(), self._press_start)
                if duration >= 800:
                    # Long press: full reset including surface normal
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
                    # Short press: wait 1s for device to settle, then capture
                    self._done_at = time.ticks_add(time.ticks_ms(), _SETTLE_MS)
                    self._phase   = 'settling'

        elif self._phase == 'settling':
            if time.ticks_diff(time.ticks_ms(), self._done_at) >= 0:
                self._samples    = []
                self._sample_end = time.ticks_add(time.ticks_ms(), _SAMPLE_MS)
                self._phase      = 'sampling'

        elif self._phase == 'sampling':
            g = sensor.get_gravity()
            if g is not None:
                self._samples.append(g)

            done = (time.ticks_diff(time.ticks_ms(), self._sample_end) >= 0
                    or len(self._samples) >= _SAMPLE_N)
            if done:
                if self._samples:
                    n  = len(self._samples)
                    ax = sum(s[0] for s in self._samples) / n
                    ay = sum(s[1] for s in self._samples) / n
                    az = sum(s[2] for s in self._samples) / n
                    mag = math.sqrt(ax*ax + ay*ay + az*az)
                    if mag > 0.5:
                        nx, ny, nz = ax/mag, ay/mag, az/mag
                        sensor.set_surface_normal(nx, ny, nz)
                        settings.surface_normal = (nx, ny, nz)
                # board_offset is 0 by definition: arccos(dot(n, n)) = arccos(1) = 0°
                settings.board_offset      = 0.0
                settings.calibrated_offset = 0.0
                settings.target_angle      = 0.0
                settings.save()
                engine.board_offset      = 0.0
                engine.calibrated_offset = 0.0
                engine.smooth_angle      = 0.0
                display.show_reboot_confirm("Saved!", "DONE")
                self._done_at = time.ticks_add(time.ticks_ms(), 800)
                self._phase   = 'feedback'

        return None
