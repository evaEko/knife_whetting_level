import time
import math
import machine
from state import State

_SETTLE_MS = 1000


class LevelState(State):
    def __init__(self):
        self._phase       = 'wait_release'  # wait_release | measuring | timing | settling | feedback
        self._press_start = None
        self._done_at     = None
        self._action      = None  # 'save' | 'reset'

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
                # Capture the full gravity vector as the surface normal.
                # arccos(dot(g, n)) then gives surface inclination invariant
                # to sensor spinning on the blade, regardless of mounting orientation.
                g = sensor.get_gravity()
                if g is not None:
                    mag = math.sqrt(g[0]*g[0] + g[1]*g[1] + g[2]*g[2])
                    if mag > 0.5:
                        nx, ny, nz = g[0]/mag, g[1]/mag, g[2]/mag
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
