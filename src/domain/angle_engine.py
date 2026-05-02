from config import SMOOTHING, DEVIATION_THRESHOLD


class AngleEngine:
    def __init__(self, board_offset=0.0, calibrated_offset=0.0,
                 target_angle=0.0, angle_format="1d_half"):
        self.board_offset      = board_offset
        self.calibrated_offset = calibrated_offset
        self.target_angle      = target_angle
        self.target_name       = None
        self.angle_format      = angle_format
        self.raw_angle         = 0.0
        self.smooth_angle      = 0.0
        self.smoothing          = SMOOTHING
        self.deviation_threshold = DEVIATION_THRESHOLD

    def update(self, raw):
        """Apply offsets, wrap to ±180, and smooth. Call with every IMU reading."""
        self.raw_angle = raw
        angle = raw - self.board_offset - self.calibrated_offset
        while angle >  180.0: angle -= 360.0
        while angle < -180.0: angle += 360.0
        if abs(angle - self.smooth_angle) > 180.0:
            self.smooth_angle = angle
        else:
            self.smooth_angle = self.smoothing * self.smooth_angle + (1.0 - self.smoothing) * angle

    def calibrate(self):
        """Lock current raw reading as the zero reference."""
        self.calibrated_offset = self.raw_angle - self.board_offset
        self.smooth_angle = 0.0

    def set_target(self, angle, name=None):
        self.target_angle = abs(angle)
        self.target_name  = name
        self.smooth_angle = 0.0

    def clear_target(self):
        self.target_angle = 0.0
        self.target_name  = None
        self.smooth_angle = 0.0

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
