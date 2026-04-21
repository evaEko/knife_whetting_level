import struct
import time

# BMI160 registers
_CHIP_ID    = 0x00
_CMD        = 0x7E
_ACC_DATA   = 0x12  # 6 bytes: ax_l, ax_h, ay_l, ay_h, az_l, az_h
_GYR_DATA   = 0x0C  # 6 bytes
_ACC_CONF   = 0x40
_ACC_RANGE  = 0x41
_GYR_CONF   = 0x42
_GYR_RANGE  = 0x43

# Commands
_CMD_ACC_NORMAL = 0x11
_CMD_GYR_NORMAL = 0x15

# Sensitivity
# Accel ±2g -> 16384 LSB/g
# Gyro ±250 dps -> 131.2 LSB/dps
ACC_SENS = 16384.0
GYR_SENS = 131.2


class BMI160:
    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr
        self.gx_bias = 0.0
        self.gy_bias = 0.0
        self.gz_bias = 0.0
        self._init()

    def _write(self, reg, val):
        self.i2c.writeto_mem(self.addr, reg, bytes([val]))

    def _read(self, reg, n):
        return self.i2c.readfrom_mem(self.addr, reg, n)

    def _init(self):
        chip_id = self._read(_CHIP_ID, 1)[0]
        if chip_id != 0xD1:
            raise RuntimeError(f"BMI160 not found, chip_id=0x{chip_id:02X}")

        # Enable accelerometer and gyroscope
        self._write(_CMD, _CMD_ACC_NORMAL)
        time.sleep_ms(100)
        self._write(_CMD, _CMD_GYR_NORMAL)
        time.sleep_ms(100)

        # ±2g, 800Hz (0x2B = ODR 800Hz, bwp normal)
        self._write(_ACC_RANGE, 0x03)
        self._write(_ACC_CONF, 0x2B)

        # ±250 dps, 800Hz
        self._write(_GYR_RANGE, 0x03)
        self._write(_GYR_CONF, 0x2B)

    def read_accel(self):
        """Returns (ax, ay, az) in g"""
        d = self._read(_ACC_DATA, 6)
        ax, ay, az = struct.unpack('<hhh', d)
        return ax / ACC_SENS, ay / ACC_SENS, az / ACC_SENS

    def read_gyro(self):
        """Returns (gx, gy, gz) in dps"""
        d = self._read(_GYR_DATA, 6)
        gx, gy, gz = struct.unpack('<hhh', d)
        return gx / GYR_SENS, gy / GYR_SENS, gz / GYR_SENS

    def calibrate_gyro(self, samples=200):
        """Average gyro readings at rest to measure zero-rate bias."""
        sx = sy = sz = 0.0
        for _ in range(samples):
            gx, gy, gz = self.read_gyro()
            sx += gx
            sy += gy
            sz += gz
            time.sleep_ms(5)
        self.gx_bias = sx / samples
        self.gy_bias = sy / samples
        self.gz_bias = sz / samples

    def suspend(self):
        """Put accelerometer and gyroscope into suspend mode."""
        self._write(_CMD, 0x10)  # acc suspend
        time.sleep_ms(50)
        self._write(_CMD, 0x14)  # gyr suspend
        time.sleep_ms(50)

    def read_all(self):
        """Returns (ax, ay, az, gx, gy, gz) in one I2C burst read."""
        d = self._read(_GYR_DATA, 12)
        gx, gy, gz, ax, ay, az = struct.unpack('<hhhhhh', d)
        return (ax / ACC_SENS, ay / ACC_SENS, az / ACC_SENS,
                gx / GYR_SENS - self.gx_bias,
                gy / GYR_SENS - self.gy_bias,
                gz / GYR_SENS - self.gz_bias)
