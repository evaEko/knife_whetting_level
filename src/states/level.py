import time
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
                    # Long press: reset to zero — no need to settle
                    settings.reset_board_offset()
                    settings.reset_calibration()
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
                settings.save_board_offset(engine.raw_angle)
                settings.reset_calibration()
                engine.board_offset      = engine.raw_angle
                engine.calibrated_offset = 0.0
                engine.smooth_angle      = 0.0
                display.show_reboot_confirm("Saved!", "DONE")
                self._done_at = time.ticks_add(time.ticks_ms(), 800)
                self._phase   = 'feedback'

        return None
