from utime import ticks_ms, ticks_diff
from helpers.pitch_calculator import pitch

_DRIFT_VEL_THRESHOLD = 0.10
_DRIFT_DEV_THRESHOLD = 1.0
_SPIKE_THRESHOLD     = 25.0
_ALPHA_FROZEN        = 0.995
_ALPHA_ACTIVE        = 0.70
_LOG_INTERVAL        = 500


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
        self._smooth(pitch(g, self._calibration.n_stone))
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
            alpha = _ALPHA_FROZEN
        elif smooth_vel >= _DRIFT_VEL_THRESHOLD or deviation >= _DRIFT_DEV_THRESHOLD:
            alpha = _ALPHA_ACTIVE
        else:
            alpha = _ALPHA_FROZEN
        self._prev_pitch = self._pitch
        self._pitch = alpha * self._pitch + (1.0 - alpha) * raw

    def reset_pitch(self):
        self._pitch = None
        self._prev_pitch = None

    def pitch(self):
        return self._pitch if self._pitch is not None else 0.0

    def in_position(self):
        if self._pitch is None:
            return False
        target = self._calibration.target_angle()
        if target is None:
            return False
        return abs(self._pitch - target) <= self._config.deviation_threshold
