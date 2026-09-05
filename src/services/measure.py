from utime import ticks_ms, ticks_diff
from helpers.angle_calculator import calculate_angle, spin_rate
from services.logging import log

_DRIFT_VEL_THRESHOLD = 0.10
_DRIFT_DEV_THRESHOLD = 0.4
_SPIKE_THRESHOLD     = 10.0
_SPIN_THRESHOLD      = 0.5     # rad/s, matches the old is_spinning() default
_ALPHA_FROZEN        = 0.995
_ALPHA_ACTIVE        = 0.70
_LOG_INTERVAL        = 500


class MeasureService:
    def __init__(self, imu_service, calibration_service, config_service):
        self._imu         = imu_service
        self._calibration = calibration_service
        self._config      = config_service
        self._angle       = None
        self._prev_angle  = None
        self._last_log    = 0

    def update(self):
        raw = self._read_raw_angle()
        if raw is None:
            return False
        self._smooth(raw)
        self._log_periodically()
        return True

    def _read_raw_angle(self):
        """Fresh gravity sample -> raw blade angle, or None if no new data / no calibration."""
        if not self._imu.update():
            return None
        if not self._calibration.has_stone():
            return None
        gravity = self._imu.get_gravity()
        return calculate_angle(gravity, self._calibration.n_stone)

    def _smooth(self, raw):
        if self._angle is None:
            self._angle = raw
            self._prev_angle = raw
            return
        self._snap_if_stopped(raw)
        alpha = self._select_alpha(raw)
        self._prev_angle = self._angle
        self._angle = alpha * self._angle + (1.0 - alpha) * raw

    def _snap_if_stopped(self, raw):
        """If the filter is lost after a coin-spin but that spin has stopped, snap to raw."""
        if not self._is_spinning_on_stone() and abs(raw - self._angle) >= _SPIKE_THRESHOLD:
            self._angle = raw
            self._prev_angle = raw

    def _is_spinning_on_stone(self):
        """True while rotating fast about the n_stone axis (the magnet coin-spin that can
        cause transient quaternion drift). Rotation about any other axis — e.g. tilting the
        blade while sharpening — doesn't count, so real motion isn't mistaken for a spin."""
        gyro = self._imu.get_angular_velocity()
        return spin_rate(gyro, self._calibration.n_stone) >= _SPIN_THRESHOLD

    def _select_alpha(self, raw):
        """Freeze on spikes, track quickly while moving, hold steady otherwise."""
        smooth_vel = abs(self._angle - self._prev_angle)
        deviation  = abs(raw - self._angle)
        if deviation >= _SPIKE_THRESHOLD:
            return _ALPHA_FROZEN
        if smooth_vel >= _DRIFT_VEL_THRESHOLD or deviation >= _DRIFT_DEV_THRESHOLD:
            return _ALPHA_ACTIVE
        return _ALPHA_FROZEN

    def _log_periodically(self):
        if ticks_diff(ticks_ms(), self._last_log) >= _LOG_INTERVAL:
            self._last_log = ticks_ms()
            log("angle={:.2f}".format(self.angle()))

    def reset_angle(self):
        self._angle = None
        self._prev_angle = None

    def angle(self):
        return self._angle if self._angle is not None else 0.0

    def in_position(self):
        if self._angle is None:
            return False
        target = self._calibration.target_angle()
        if target is None:
            return False
        return abs(self._angle - target) <= self._config.deviation_threshold
