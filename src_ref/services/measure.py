from utime import ticks_ms, ticks_diff
from helpers.pitch_calculator import PitchCalculator

_DRIFT_VEL_THRESHOLD = 0.10   # °/tick — smooth velocity below this = stationary/drift
_DRIFT_DEV_THRESHOLD = 1.0    # degrees — deviation above this triggers active alpha
_SPIKE_THRESHOLD     = 25.0   # degrees — deviation above this is an outlier, use frozen
_ALPHA_FROZEN        = 0.995  # weight on OLD when stationary — display essentially frozen
_ALPHA_ACTIVE        = 0.70   # weight on OLD when moving — matches src default SMOOTHING
_LOG_INTERVAL        = 500    # ms between pitch log lines


class MeasureService:
    def __init__(self, imu_service, calibration_service, config_service, logging_service):
        self._imu         = imu_service
        self._calibration = calibration_service
        self._config      = config_service
        self._log         = logging_service
        self._pitch       = None
        self._prev_pitch  = None
        self._last_log    = 0

    def update(self):
        if not self._imu.update():
            return False
        if not self._calibration.has_stone():
            return False
        g = self._imu.get_gravity()
        self._smooth(PitchCalculator.pitch(g, self._calibration.n_stone))
        # Log pitch at regular intervals for debugging/analysis
        if ticks_diff(ticks_ms(), self._last_log) >= _LOG_INTERVAL:
            self._last_log = ticks_ms()
            self._log.log("pitch={:.2f}".format(self.pitch()))
        return True

    def _smooth(self, raw):
        if self._pitch is None:
            self._pitch = raw
            self._prev_pitch = raw
            return
        smooth_vel = abs(self._pitch - self._prev_pitch)
        deviation  = abs(raw - self._pitch)
        if deviation >= _SPIKE_THRESHOLD:
            alpha = _ALPHA_FROZEN                          # outlier — ignore
        elif smooth_vel >= _DRIFT_VEL_THRESHOLD or deviation >= _DRIFT_DEV_THRESHOLD:
            alpha = _ALPHA_ACTIVE                          # real movement
        else:
            alpha = _ALPHA_FROZEN                          # stationary
        self._prev_pitch = self._pitch
        self._pitch = alpha * self._pitch + (1.0 - alpha) * raw

    def reset_pitch(self):
        self._pitch = None
        self._prev_pitch = None

    def pitch(self):
        return self._pitch if self._pitch is not None else 0.0

    def in_position(self):
        """True when pitch is within deviation_threshold of target_angle."""
        if self._pitch is None:
            return False
        target = self._calibration.target_angle()
        if target is None:
            return False
        return abs(self._pitch - target) <= self._config.deviation_threshold

