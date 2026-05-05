import time
import machine
from state import State

_SETTLE_MS = 1000
_SAMPLE_MS = 500
_SAMPLE_N  = 20


class LevelState(State):
    def __init__(self):
        self._phase       = 'wait_release'  # wait_release | prompt_a | timing_a | settling_a | sampling_a | prompt_b | timing_b | settling_b | sampling_b | feedback
        self._press_start = None
        self._done_at     = None
        self._samples     = []
        self._sample_end  = None
        self._mean_a      = None

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

        raw = sensor.update()
        if raw is not None:
            engine.raw_angle = raw

        if self._phase == 'prompt_a':
            if buttons.is_pressed('low'):
                self._press_start = time.ticks_ms()
                self._phase = 'timing_a'

        elif self._phase == 'timing_a':
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
                    # Clear surface normal so sensor returns raw IMU inclination
                    sensor.clear_surface_normal()
                    self._done_at = time.ticks_add(time.ticks_ms(), _SETTLE_MS)
                    self._phase   = 'settling_a'

        elif self._phase == 'settling_a':
            if time.ticks_diff(time.ticks_ms(), self._done_at) >= 0:
                self._samples    = []
                self._sample_end = time.ticks_add(time.ticks_ms(), _SAMPLE_MS)
                self._phase      = 'sampling_a'

        elif self._phase == 'sampling_a':
            if raw is not None:
                self._samples.append(raw)
            done = (time.ticks_diff(time.ticks_ms(), self._sample_end) >= 0
                    or len(self._samples) >= _SAMPLE_N)
            if done and self._samples:
                self._mean_a = sum(self._samples) / len(self._samples)
                display.show_message("Flip ~180", "low=press")
                self._phase = 'prompt_b'

        elif self._phase == 'prompt_b':
            if buttons.is_pressed('low'):
                self._press_start = time.ticks_ms()
                self._phase = 'timing_b'

        elif self._phase == 'timing_b':
            if not buttons.is_pressed('low'):
                self._done_at = time.ticks_add(time.ticks_ms(), _SETTLE_MS)
                self._phase   = 'settling_b'

        elif self._phase == 'settling_b':
            if time.ticks_diff(time.ticks_ms(), self._done_at) >= 0:
                self._samples    = []
                self._sample_end = time.ticks_add(time.ticks_ms(), _SAMPLE_MS)
                self._phase      = 'sampling_b'

        elif self._phase == 'sampling_b':
            if raw is not None:
                self._samples.append(raw)
            done = (time.ticks_diff(time.ticks_ms(), self._sample_end) >= 0
                    or len(self._samples) >= _SAMPLE_N)
            if done and self._samples:
                mean_b  = sum(self._samples) / len(self._samples)
                offset  = (self._mean_a + mean_b) / 2.0
                settings.surface_normal    = None
                settings.board_offset      = offset
                settings.calibrated_offset = 0.0
                settings.target_angle      = 0.0
                settings.save()
                engine.board_offset      = offset
                engine.calibrated_offset = 0.0
                engine.smooth_angle      = 0.0
                display.show_reboot_confirm("Saved!", "DONE")
                self._done_at = time.ticks_add(time.ticks_ms(), 800)
                self._phase   = 'feedback'

        return None
