from machine import I2C, Pin
from drivers.bno085 import IMU


class ImuService:
    def __init__(self, sda_pin, scl_pin, i2c_id, addr):
        self._sda_pin = sda_pin
        self._scl_pin = scl_pin
        self._i2c_id  = i2c_id
        self._addr    = addr
        self._imu     = None

    def init(self):
        i2c = I2C(self._i2c_id,
                  sda=Pin(self._sda_pin),
                  scl=Pin(self._scl_pin),
                  freq=400_000)
        self._imu = IMU(i2c, addr=self._addr)

    def update(self):
        """Drain packets, update quaternion. Returns True if new data."""
        return self._imu.update()

    def get_gravity(self):
        """Returns (gx, gy, gz) unit vector."""
        return self._imu.get_gravity()

    def get_angular_velocity(self):
        """Returns (wx, wy, wz) in rad/s."""
        return self._imu.get_angular_velocity()
