import struct
import time
import math

# SHTP channels
_CHAN_CONTROL = 2
_CHAN_REPORTS = 3

# SH-2 report IDs
_ROTATION_VECTOR = 0x05
_GAME_ROTATION_VECTOR = 0x08
_SET_FEATURE_CMD = 0xFD
_BASE_TIMESTAMP = 0xFB

_Q14 = 16384.0
_MAX_PACKET = 128


class BNO085:
    def __init__(self, i2c, addr=0x4A, rst=None):
        self.i2c = i2c
        self.addr = addr
        self._seq = [0] * 6
        self._quat = (1.0, 0.0, 0.0, 0.0)  # w, x, y, z

        # Hardware reset if pin provided
        if rst is not None:
            rst.value(0)
            time.sleep_ms(10)
            rst.value(1)
            time.sleep_ms(100)

        # Wait for boot and drain startup packets
        time.sleep_ms(200)
        for _ in range(10):
            self._read_packet()
            time.sleep_ms(10)

    def _read_packet(self):
        """Read one SHTP packet. Returns (channel, payload) or None."""
        try:
            header = self.i2c.readfrom(self.addr, 4)
        except OSError:
            return None

        length = (header[1] & 0x7F) << 8 | header[0]
        if length < 4 or length > 32768:
            return None

        read_len = min(length, _MAX_PACKET)
        try:
            data = self.i2c.readfrom(self.addr, read_len)
        except OSError:
            return None

        channel = data[2]
        payload = data[4:read_len]
        return (channel, payload)

    def _send_packet(self, channel, payload):
        """Send an SHTP packet."""
        length = len(payload) + 4
        header = bytes([
            length & 0xFF,
            (length >> 8) & 0x7F,
            channel,
            self._seq[channel]
        ])
        self._seq[channel] = (self._seq[channel] + 1) & 0xFF
        self.i2c.writeto(self.addr, header + bytes(payload))

    def enable_rotation_vector(self, interval_ms=10):
        """Enable game rotation vector (accel+gyro, no mag) at given interval."""
        interval_us = interval_ms * 1000
        cmd = bytearray(17)
        cmd[0] = _SET_FEATURE_CMD
        cmd[1] = _GAME_ROTATION_VECTOR
        struct.pack_into('<I', cmd, 5, interval_us)
        self._send_packet(_CHAN_CONTROL, cmd)
        time.sleep_ms(50)
        # Drain response packets
        for _ in range(5):
            self._read_packet()
            time.sleep_ms(10)

    def update(self):
        """Drain all available packets and update quaternion. Returns True if new data."""
        got_data = False
        for _ in range(20):  # read up to 20 queued packets
            result = self._read_packet()
            if result is None:
                break
            channel, payload = result
            if channel == _CHAN_REPORTS and len(payload) >= 1:
                if self._parse_reports(payload):
                    got_data = True
        return got_data

    def _parse_reports(self, payload):
        """Parse sensor reports from input report channel."""
        i = 0
        got_rv = False
        while i < len(payload):
            report_id = payload[i]
            if report_id == _BASE_TIMESTAMP and i + 5 <= len(payload):
                i += 5
            elif report_id == _GAME_ROTATION_VECTOR and i + 12 <= len(payload):
                qi = struct.unpack_from('<h', payload, i + 4)[0] / _Q14
                qj = struct.unpack_from('<h', payload, i + 6)[0] / _Q14
                qk = struct.unpack_from('<h', payload, i + 8)[0] / _Q14
                qr = struct.unpack_from('<h', payload, i + 10)[0] / _Q14
                self._quat = (qr, qi, qj, qk)  # w, x, y, z
                got_rv = True
                i += 12
            else:
                break
        return got_rv

    def get_roll(self):
        """Roll angle (rotation around X axis) in degrees, +/-180."""
        w, x, y, z = self._quat
        roll = math.degrees(math.atan2(
            2.0 * (w * x + y * z),
            1.0 - 2.0 * (x * x + y * y)))
        if roll > 180.0:
            roll -= 360.0
        elif roll < -180.0:
            roll += 360.0
        return roll

    def get_pitch(self):
        """Pitch angle (rotation around Y axis) in degrees, +/-90."""
        w, x, y, z = self._quat
        pitch = math.degrees(math.asin(max(-1.0, min(1.0, 2.0 * (w * y - z * x)))))
        return pitch

    def get_gravity(self):
        """Gravity unit vector in sensor body frame (gx, gy, gz), derived from quaternion."""
        w, x, y, z = self._quat
        return (
            2.0 * (w * y - x * z),
            -2.0 * (y * z + x * w),
            2.0 * (x * x + y * y) - 1.0,
        )

    def get_inclination(self):
        """Surface inclination in degrees [0, 90] using Z axis only.
        Fallback when no surface normal has been calibrated."""
        _, _, gz = self.get_gravity()
        return math.degrees(math.acos(max(-1.0, min(1.0, abs(gz)))))

    def set_report_interval(self, interval_ms):
        """Change rotation vector report interval. Use 1000+ for low-power idle."""
        interval_us = interval_ms * 1000
        cmd = bytearray(17)
        cmd[0] = _SET_FEATURE_CMD
        cmd[1] = _GAME_ROTATION_VECTOR
        struct.pack_into('<I', cmd, 5, interval_us)
        self._send_packet(_CHAN_CONTROL, cmd)
        time.sleep_ms(50)
        for _ in range(5):
            self._read_packet()
            time.sleep_ms(10)

    def suspend(self):
        """Soft-reset into sleep — on wake, just hard-reset or re-init."""
        pass
