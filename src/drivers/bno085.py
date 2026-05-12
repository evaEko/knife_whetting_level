import struct
import time

# SHTP channels
_CHAN_CONTROL = 2
_CHAN_REPORTS = 3

# SH-2 report IDs
_GAME_ROTATION_VECTOR = 0x08
_SET_FEATURE_CMD      = 0xFD
_BASE_TIMESTAMP       = 0xFB
_COMMAND_REQUEST      = 0xF2

# SH-2 command IDs
_CMD_ME_CALIBRATE = 0x07

_Q14        = 16384.0
_MAX_PACKET = 128


class BNO085:
    """Static driver — knows the BNO085 SHTP protocol. No state."""

    @staticmethod
    def read_packet(i2c, addr):
        """Read one SHTP packet. Returns (channel, payload) or None."""
        try:
            header = i2c.readfrom(addr, 4)
        except OSError:
            return None
        length = (header[1] & 0x7F) << 8 | header[0]
        if length < 4 or length > 32768:
            return None
        read_len = min(length, _MAX_PACKET)
        try:
            data = i2c.readfrom(addr, read_len)
        except OSError:
            return None
        return (data[2], data[4:read_len])

    @staticmethod
    def send_packet(i2c, addr, seq, channel, payload):
        """Send one SHTP packet. Returns updated seq array."""
        length = len(payload) + 4
        header = bytes([
            length & 0xFF,
            (length >> 8) & 0x7F,
            channel,
            seq[channel],
        ])
        seq[channel] = (seq[channel] + 1) & 0xFF
        i2c.writeto(addr, header + bytes(payload))
        return seq

    @staticmethod
    def _enable_report(i2c, addr, seq, report_id, interval_ms):
        interval_us = interval_ms * 1000
        cmd = bytearray(17)
        cmd[0] = _SET_FEATURE_CMD
        cmd[1] = report_id
        struct.pack_into('<I', cmd, 5, interval_us)
        seq = BNO085.send_packet(i2c, addr, seq, _CHAN_CONTROL, cmd)
        time.sleep_ms(50)
        for _ in range(5):
            BNO085.read_packet(i2c, addr)
            time.sleep_ms(10)
        return seq

    @staticmethod
    def enable_rotation_vector(i2c, addr, seq, interval_ms=10):
        """Enable game rotation vector report."""
        return BNO085._enable_report(i2c, addr, seq, _GAME_ROTATION_VECTOR, interval_ms)

    @staticmethod
    def configure_calibration(i2c, addr, seq, accel=True, gyro=True, mag=False):
        """Configure dynamic calibration per sensor."""
        cmd = bytearray(12)
        cmd[0] = _COMMAND_REQUEST
        cmd[1] = 0
        cmd[2] = _CMD_ME_CALIBRATE
        cmd[3] = 0
        cmd[4] = 1 if accel else 0
        cmd[5] = 1 if gyro  else 0
        cmd[6] = 1 if mag   else 0
        seq = BNO085.send_packet(i2c, addr, seq, _CHAN_CONTROL, cmd)
        time.sleep_ms(50)
        for _ in range(5):
            BNO085.read_packet(i2c, addr)
            time.sleep_ms(10)
        return seq

    @staticmethod
    def parse_reports(payload):
        """Parse sensor reports. Returns quaternion (w,x,y,z) or None."""
        i = 0
        while i < len(payload):
            report_id = payload[i]
            if report_id == _BASE_TIMESTAMP and i + 5 <= len(payload):
                i += 5
            elif report_id == _GAME_ROTATION_VECTOR and i + 12 <= len(payload):
                qi = struct.unpack_from('<h', payload, i + 4)[0] / _Q14
                qj = struct.unpack_from('<h', payload, i + 6)[0] / _Q14
                qk = struct.unpack_from('<h', payload, i + 8)[0] / _Q14
                qr = struct.unpack_from('<h', payload, i + 10)[0] / _Q14
                return (qr, qi, qj, qk)
            else:
                break
        return None


class IMU:
    """Instance — owns i2c connection, seq counters and latest quaternion for one BNO085 chip."""

    def __init__(self, i2c, addr=0x4A, rst=None):
        self.i2c   = i2c
        self.addr  = addr
        self._seq  = [0] * 6
        self._quat = (1.0, 0.0, 0.0, 0.0)  # w, x, y, z

        if rst is not None:
            rst.value(0)
            time.sleep_ms(10)
            rst.value(1)
            time.sleep_ms(100)

        time.sleep_ms(200)
        for _ in range(10):
            BNO085.read_packet(self.i2c, self.addr)
            time.sleep_ms(10)

        self._seq = BNO085.enable_rotation_vector(self.i2c, self.addr, self._seq)

    def update(self):
        """Drain all available packets, update quaternion. Returns True if new data."""
        got_data = False
        for _ in range(20):
            result = BNO085.read_packet(self.i2c, self.addr)
            if result is None:
                break
            channel, payload = result
            if channel == _CHAN_REPORTS and len(payload) >= 1:
                quat = BNO085.parse_reports(payload)
                if quat is not None:
                    self._quat = quat
                    got_data = True
        return got_data

    def get_gravity(self):
        """Gravity unit vector derived from quaternion (gx, gy, gz)."""
        w, x, y, z = self._quat
        return (
            2.0 * (w * y - x * z),
            -2.0 * (y * z + x * w),
            2.0 * (x * x + y * y) - 1.0,
        )

