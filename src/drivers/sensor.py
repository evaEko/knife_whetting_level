import time
from machine import I2C, Pin
from config import SDA_IMU, SCL_IMU, BNO085_ADDR, ANGLE_AXIS
from drivers.bno085 import BNO085

_IDLE_TIMEOUT       = 60_000
_MOVEMENT_THRESHOLD = 0.5
_INTERVAL_ACTIVE    = 10
_INTERVAL_IDLE      = 1000


class Sensor:
    def __init__(self):
        self._imu          = None
        self._idle         = False
        self._last_move    = 0
        self._idle_ref     = 0.0
        self._axis         = ANGLE_AXIS

    def init(self):
        try:
            if self._axis not in ("pitch", "roll"):
                print(f"Invalid ANGLE_AXIS '{self._axis}', using 'pitch'")
                self._axis = "pitch"
            self._imu = BNO085(
                I2C(0, sda=Pin(SDA_IMU), scl=Pin(SCL_IMU), freq=400000),
                addr=BNO085_ADDR
            )
            self._imu.enable_rotation_vector(interval_ms=_INTERVAL_ACTIVE)
            self._last_move = time.ticks_ms()
            print(f"IMU OK ({self._axis})")
        except Exception as e:
            print(f"IMU ERROR: {e}")

    @property
    def ready(self):
        return self._imu is not None

    def update(self):
        """Read latest configured axis from IMU, manage idle rate. Returns angle or None on error."""
        if not self._imu:
            return None
        try:
            self._imu.update()
            if self._axis == "roll":
                raw = self._imu.get_roll()
            else:
                raw = self._imu.get_pitch()
            self._update_idle(raw)
            return raw
        except OSError:
            time.sleep_ms(5)
            return None

    def _update_idle(self, raw):
        now = time.ticks_ms()
        if abs(raw - self._idle_ref) >= _MOVEMENT_THRESHOLD:
            self._idle_ref  = raw
            self._last_move = now
            if self._idle:
                self._imu.set_report_interval(_INTERVAL_ACTIVE)
                self._idle = False
        elif not self._idle and time.ticks_diff(now, self._last_move) >= _IDLE_TIMEOUT:
            self._imu.set_report_interval(_INTERVAL_IDLE)
            self._idle = True
