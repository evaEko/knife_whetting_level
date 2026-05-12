from config import SMOOTHING, DEVIATION_THRESHOLD

# When the smoothed angle is moving slower than this threshold (°/tick), treat
# the change as sensor drift and raise alpha to hold the previous reading.
# At 100 Hz (10 ms ticks) 0.10°/tick = 10°/s — below real sharpening motion.
_DRIFT_VEL_THRESHOLD = 0.10   # °/tick — anything slower than 10°/s treated as drift
_DRIFT_ALPHA_FROZEN  = 0.995  # alpha when drift detected — display is essentially frozen


class AngleEngine:
    def __init__(self, board_offset=0.0, calibrated_offset=0.0,
                 target_angle=0.0, angle_format="1d_half"):
        self.board_offset        = board_offset
        self.calibrated_offset   = calibrated_offset
        self.target_angle        = target_angle
        self.target_name         = None
        self.angle_format        = angle_format
        self.raw_angle           = 0.0
        self.smooth_angle        = 0.0
        self.smoothing           = SMOOTHING
        self.deviation_threshold = DEVIATION_THRESHOLD
        self._prev_smooth        = 0.0   # smooth_angle from the previous tick

    def update(self, raw):
        """Apply offsets, wrap to ±180, and smooth. Call with every IMU reading."""
        self.raw_angle = raw
        angle = raw - self.board_offset - self.calibrated_offset
        while angle >  180.0: angle -= 360.0
        while angle < -180.0: angle += 360.0
        if abs(angle - self.smooth_angle) > 180.0:
            self.smooth_angle = angle
        else:
            # Adaptive alpha: when the smoothed angle is barely moving
            # (slow rotation / drift), hold the previous value more tightly.
            # Using smoothed velocity rather than raw avoids reacting to noise.
            smooth_vel = abs(self.smooth_angle - self._prev_smooth)
            if smooth_vel < _DRIFT_VEL_THRESHOLD:
                alpha = _DRIFT_ALPHA_FROZEN
            else:
                alpha = self.smoothing
            self._prev_smooth = self.smooth_angle
            self.smooth_angle = alpha * self.smooth_angle + (1.0 - alpha) * angle

    def calibrate(self):
        """Lock current raw reading as the zero reference."""
        self.calibrated_offset = self.raw_angle - self.board_offset
        self.smooth_angle  = 0.0
        self._prev_smooth  = 0.0

    def set_target(self, angle, name=None):
        self.target_angle = abs(angle)
        self.target_name  = name
        self.smooth_angle  = 0.0
        self._prev_smooth  = 0.0

    def clear_target(self):
        self.target_angle = 0.0
        self.target_name  = None
        self.smooth_angle  = 0.0
        self._prev_smooth  = 0.0

    def apply(self, settings):
        """Sync engine state from persisted settings."""
        self.board_offset      = settings.board_offset
        self.calibrated_offset = settings.calibrated_offset
        self.target_angle      = abs(settings.target_angle)
        self.angle_format      = settings.angle_format

    @property
    def on_target(self):
        """True when no target is set, or blade magnitude is within threshold of target."""
        target = abs(self.target_angle)
        if target == 0.0:
            return True
        return abs(abs(self.smooth_angle) - target) <= self.deviation_threshold

    @property
    def on_stone(self):
        """True when the blade appears to be in the sharpening position.
        Requires a target angle to be set; uses 6× deviation_threshold as the
        tolerance to allow for technique variation without false lift triggers."""
        target = abs(self.target_angle)
        if target == 0.0:
            return True  # no target — cannot detect, assume on stone
        return abs(abs(self.smooth_angle) - target) <= self.deviation_threshold * 6
