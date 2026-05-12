import time
import math
from machine import I2C, Pin
from config import SDA_IMU, SCL_IMU, BNO085_ADDR
from drivers.bno085 import BNO085

_IDLE_TIMEOUT            = 60_000
_MOVEMENT_THRESHOLD      = 0.5
_INTERVAL_ACTIVE         = 10
_INTERVAL_IDLE           = 1000
_ON_STONE_COS_THRESHOLD  = 0.94   # cos(20°) — max orientation deviation from calibrated position
_LIFT_DEBOUNCE_MS        = 1000    # ms blade must stay at correct orientation before "on stone" is declared


class Sensor:
    def __init__(self):
        self._imu            = None
        self._idle           = False
        self._last_move      = 0
        self._idle_ref       = 0.0
        self._surface_normal = None  # (nx, ny, nz) unit vector, captured during Level cal
        self._calibrated_g        = None  # (gx, gy, gz) gravity unit vector at calibration position
        self._on_stone            = True  # raw check: False when orientation deviates
        self._on_stone_debounced  = True  # reported value: True→False is immediate; False→True needs 600ms
        self._on_stone_true_since = 0     # ticks_ms when raw _on_stone last became True after being False

    def init(self):
        try:
            self._imu = BNO085(
                I2C(0, sda=Pin(SDA_IMU), scl=Pin(SCL_IMU), freq=400000),
                addr=BNO085_ADDR
            )
            self._imu.enable_rotation_vector(interval_ms=_INTERVAL_ACTIVE)
            self._imu.configure_calibration(accel=True, gyro=False, mag=False)
            self._last_move = time.ticks_ms()
            print("IMU OK")
        except Exception as e:
            print(f"IMU ERROR: {e}")

    @property
    def ready(self):
        return self._imu is not None

    def set_surface_normal(self, nx, ny, nz):
        self._surface_normal = (nx, ny, nz)

    def clear_surface_normal(self):
        self._surface_normal = None

    def set_calibrated_g(self, gx, gy, gz):
        self._calibrated_g = (gx, gy, gz)

    def clear_calibrated_g(self):
        self._calibrated_g        = None
        self._on_stone            = True
        self._on_stone_debounced  = True
        self._on_stone_true_since = 0

    @property
    def on_stone(self):
        return self._on_stone_debounced

    def get_gravity(self):
        """Current gravity unit vector in sensor body frame, or None if not ready."""
        if not self._imu:
            return None
        return self._imu.get_gravity()

    def update(self):
        """Read surface inclination from IMU. Returns angle in degrees or None on error."""
        if not self._imu:
            return None
        try:
            self._imu.update()
            gx, gy, gz = self._imu.get_gravity()
            if self._calibrated_g is not None:
                cx, cy, cz = self._calibrated_g
                self._on_stone = (gx*cx + gy*cy + gz*cz) >= _ON_STONE_COS_THRESHOLD
            if self._on_stone:
                if not self._on_stone_debounced:
                    now = time.ticks_ms()
                    if self._on_stone_true_since == 0:
                        self._on_stone_true_since = now
                    elif time.ticks_diff(now, self._on_stone_true_since) >= _LIFT_DEBOUNCE_MS:
                        self._on_stone_debounced  = True
                        self._on_stone_true_since = 0
            else:
                self._on_stone_debounced  = False
                self._on_stone_true_since = 0
            if self._surface_normal is not None:
                nx, ny, nz = self._surface_normal
                dot = max(-1.0, min(1.0, gx*nx + gy*ny + gz*nz))
                raw = math.degrees(math.acos(dot))
            else:
                raw = math.degrees(math.acos(max(-1.0, min(1.0, abs(gz)))))
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
