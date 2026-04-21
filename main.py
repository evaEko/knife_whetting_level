import machine
import time
import math
from machine import I2C, Pin

from config import (
    SDA_BMI, SCL_BMI, SDA_OLED, SCK_OLED, BTN_CAL,
    BMI160_ADDR, OLED_ADDR,
    DEVIATION_THRESHOLD, LONG_PRESS_MS, SMOOTHING, MADGWICK_BETA
)
from bmi160 import BMI160
from ssd1306 import SSD1306

# ── States ────────────────────────────────────────────────────────────────────
STATE_INIT        = "INIT"
STATE_READY       = "READY"
STATE_CALIBRATION = "CALIBRATION"


# ── Madgwick AHRS filter ─────────────────────────────────────────────────────
_DEG2RAD = math.pi / 180.0

class MadgwickFilter:
    def __init__(self, beta=MADGWICK_BETA):
        self.beta = beta
        # Quaternion [w, x, y, z]
        self.q0 = 1.0
        self.q1 = 0.0
        self.q2 = 0.0
        self.q3 = 0.0
        self.last_time = time.ticks_ms()

    def seed(self, ax, ay, az):
        """Initialize quaternion from accelerometer so it starts aligned."""
        # Normalize accel
        norm = math.sqrt(ax * ax + ay * ay + az * az)
        if norm < 0.01:
            return
        ax /= norm
        ay /= norm
        az /= norm
        # Compute pitch and roll from gravity
        pitch = math.atan2(-ax, az)
        roll = math.atan2(ay, math.sqrt(ax * ax + az * az))
        # Convert to quaternion (yaw = 0)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        self.q0 = cp * cr
        self.q1 = sp * cr
        self.q2 = cp * sr
        self.q3 = sp * sr

    def update(self, ax, ay, az, gx, gy, gz):
        now = time.ticks_ms()
        dt = time.ticks_diff(now, self.last_time) / 1000.0
        self.last_time = now

        q0, q1, q2, q3 = self.q0, self.q1, self.q2, self.q3

        # Convert gyro to rad/s
        gx *= _DEG2RAD
        gy *= _DEG2RAD
        gz *= _DEG2RAD

        # Gyro quaternion rate of change
        qDot0 = 0.5 * (-q1 * gx - q2 * gy - q3 * gz)
        qDot1 = 0.5 * (q0 * gx + q2 * gz - q3 * gy)
        qDot2 = 0.5 * (q0 * gy - q1 * gz + q3 * gx)
        qDot3 = 0.5 * (q0 * gz + q1 * gy - q2 * gx)

        # Accel correction (gradient descent step)
        a_norm = math.sqrt(ax * ax + ay * ay + az * az)
        if a_norm > 0.01:
            ax /= a_norm
            ay /= a_norm
            az /= a_norm

            # Precompute repeated terms
            _2q0 = 2.0 * q0
            _2q1 = 2.0 * q1
            _2q2 = 2.0 * q2
            _2q3 = 2.0 * q3
            _4q0 = 4.0 * q0
            _4q1 = 4.0 * q1
            _4q2 = 4.0 * q2
            q0q0 = q0 * q0
            q1q1 = q1 * q1
            q2q2 = q2 * q2
            q3q3 = q3 * q3

            # Gradient
            s0 = _4q0 * q2q2 + _2q2 * ax + _4q0 * q1q1 - _2q1 * ay
            s1 = _4q1 * q3q3 - _2q3 * ax + 4.0 * q0q0 * q1 - _2q0 * ay - _4q1 + 8.0 * q1q1 * q1 + 8.0 * q2q2 * q1 + _4q1 * az
            s2 = 4.0 * q0q0 * q2 + _2q0 * ax + _4q2 * q3q3 - _2q3 * ay - _4q2 + 8.0 * q1q1 * q2 + 8.0 * q2q2 * q2 + _4q2 * az
            s3 = 4.0 * q1q1 * q3 - _2q1 * ax + 4.0 * q2q2 * q3 - _2q2 * ay

            # Normalize gradient step
            s_norm = math.sqrt(s0 * s0 + s1 * s1 + s2 * s2 + s3 * s3)
            if s_norm > 0.0:
                s0 /= s_norm
                s1 /= s_norm
                s2 /= s_norm
                s3 /= s_norm

            qDot0 -= self.beta * s0
            qDot1 -= self.beta * s1
            qDot2 -= self.beta * s2
            qDot3 -= self.beta * s3

        # Integrate
        q0 += qDot0 * dt
        q1 += qDot1 * dt
        q2 += qDot2 * dt
        q3 += qDot3 * dt

        # Normalize quaternion
        norm = math.sqrt(q0 * q0 + q1 * q1 + q2 * q2 + q3 * q3)
        self.q0 = q0 / norm
        self.q1 = q1 / norm
        self.q2 = q2 / norm
        self.q3 = q3 / norm

    def get_pitch(self):
        """Extract pitch angle in degrees (rotation around Y axis)."""
        q0, q1, q2, q3 = self.q0, self.q1, self.q2, self.q3
        sinp = 2.0 * (q0 * q2 - q3 * q1)
        if sinp > 1.0:
            sinp = 1.0
        elif sinp < -1.0:
            sinp = -1.0
        return math.degrees(math.asin(sinp))

    def get_roll(self):
        """Extract roll angle in degrees (rotation around X axis), ±180."""
        q0, q1, q2, q3 = self.q0, self.q1, self.q2, self.q3
        roll = math.degrees(math.atan2(
            2.0 * (q0 * q1 + q2 * q3),
            1.0 - 2.0 * (q1 * q1 + q2 * q2)))
        if roll > 180.0:
            roll -= 360.0
        elif roll < -180.0:
            roll += 360.0
        return roll


# ── Button helper ─────────────────────────────────────────────────────────────
class Button:
    def __init__(self, pin):
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self._press_start = None

    def is_pressed(self):
        return self.pin.value() == 0

    def update(self):
        """Returns ('short', 'long', None) on release. Debounced."""
        pressed = self.is_pressed()
        if pressed and self._press_start is None:
            self._press_start = time.ticks_ms()
        elif not pressed and self._press_start is not None:
            duration = time.ticks_diff(time.ticks_ms(), self._press_start)
            self._press_start = None
            if duration < 30:
                return None
            if duration >= LONG_PRESS_MS:
                return 'long'
            return 'short'
        return None


# ── Display helpers ───────────────────────────────────────────────────────────
def display_angle(oled, angle, label=None):
    oled.fill(0)
    text = f"{angle:+.0f}"
    # Scale 2 = 16px tall, fits on 72x40 display
    char_w = 8 * 2
    x = max(0, (oled.width - len(text) * char_w) // 2)
    y = 4 if label else 12
    oled.large_text(text, x, y, scale=2)
    if label:
        oled.text(label, 0, 24, 1)
    oled.show()


def display_error(oled, msg):
    oled.fill(0)
    oled.text("ERROR:", 0, 0, 1)
    oled.text(msg[:16], 0, 12, 1)
    oled.show()


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    state          = STATE_INIT
    angle_offset   = 0.0
    smooth_angle   = 0.0
    mf             = MadgwickFilter()

    # ── INIT ──────────────────────────────────────────────────────────────────
    try:
        i2c_bmi  = I2C(0, sda=Pin(SDA_BMI),  scl=Pin(SCL_BMI),  freq=400000)
        i2c_oled = I2C(1, sda=Pin(SDA_OLED), scl=Pin(SCK_OLED), freq=400000)
        oled     = SSD1306(i2c_oled, addr=OLED_ADDR)
        bmi      = BMI160(i2c_bmi, addr=BMI160_ADDR)
        btn      = Button(BTN_CAL)
    except Exception as e:
        # Can't show on display if display failed — fall back to print
        print(f"INIT ERROR: {e}")
        return

    print("Calibrating gyro...")
    oled.fill(0)
    oled.text("HOLD STILL", 4, 12, 1)
    oled.show()
    bmi.calibrate_gyro(samples=200)
    print(f"Gyro bias: gx={bmi.gx_bias:+.2f} gy={bmi.gy_bias:+.2f} gz={bmi.gz_bias:+.2f}")

    # Seed the filter from accelerometer so it starts aligned
    ax, ay, az, _, _, _ = bmi.read_all()
    mf.seed(ax, ay, az)
    mf.last_time = time.ticks_ms()

    oled.fill(0)
    oled.text("OK", 56, 12, 1)
    oled.show()
    time.sleep_ms(500)

    state = STATE_READY
    last_display = time.ticks_ms()
    last_log = time.ticks_ms()
    DISPLAY_INTERVAL = 50  # ms between display refreshes
    LOG_INTERVAL = 500     # ms between serial log messages
    loop_count = 0

    print("Entering main loop, state=READY")

    # ── Main loop ─────────────────────────────────────────────────────────────
    while True:
        # Read sensor and update filter as fast as possible
        try:
            ax, ay, az, gx, gy, gz = bmi.read_all()
            mf.update(ax, ay, az, gx, gy, gz)
            raw_angle = mf.get_roll()
            angle = raw_angle - angle_offset
            # Wrap to ±180
            while angle > 180.0:
                angle -= 360.0
            while angle < -180.0:
                angle += 360.0
            # Prevent smoothing from interpolating through ±180 wrap
            if abs(angle - smooth_angle) > 180.0:
                smooth_angle = angle
            else:
                smooth_angle = SMOOTHING * smooth_angle + (1.0 - SMOOTHING) * angle
        except OSError:
            time.sleep_ms(5)
            continue
        event = btn.update()
        loop_count += 1

        # Only refresh display every DISPLAY_INTERVAL ms
        now = time.ticks_ms()
        update_display = time.ticks_diff(now, last_display) >= DISPLAY_INTERVAL

        # Periodic log to serial
        if time.ticks_diff(now, last_log) >= LOG_INTERVAL:
            print(f"s={state} raw={raw_angle:+.1f} a={angle:+.1f} sm={smooth_angle:+.1f} off={angle_offset:+.1f} loops={loop_count}")
            loop_count = 0
            last_log = now

        if event is not None:
            print(f"BTN EVENT: {event} (state={state})")

        # ── Long press: power off from any state ─────────────────────────────
        if event == 'long':
            print("-> POWER OFF")
            oled.fill(0)
            oled.text("OFF", 24, 16, 1)
            oled.show()
            time.sleep_ms(500)
            oled.fill(0)
            oled.show()
            oled._cmd(0xAE)  # display off
            bmi.suspend()
            # Deep sleep until button long press wakes us
            # No polling — CPU stays asleep until pin interrupt fires
            while True:
                machine.lightsleep()  # no timeout = sleep until interrupt
                # Woken by pin change; check for long press
                if btn.is_pressed():
                    start = time.ticks_ms()
                    while btn.is_pressed():
                        time.sleep_ms(10)
                    if time.ticks_diff(time.ticks_ms(), start) >= LONG_PRESS_MS:
                        print("-> WAKE UP")
                        machine.reset()
                    # Short press — ignore, go back to sleep

        # ── READY ─────────────────────────────────────────────────────────────
        if state == STATE_READY:
            if angle_offset != 0.0:
                oled.invert(abs(smooth_angle) > DEVIATION_THRESHOLD)
            if update_display:
                display_angle(oled, smooth_angle)
                last_display = now

            if event == 'short':
                print(f"-> CALIBRATION")
                state = STATE_CALIBRATION
                oled.invert(False)

        # ── CALIBRATION ───────────────────────────────────────────────────────
        elif state == STATE_CALIBRATION:
            if update_display:
                display_angle(oled, smooth_angle, label="CAL")
                last_display = now

            if event == 'short':
                angle_offset = raw_angle
                angle = 0.0
                smooth_angle = 0.0
                print(f"-> SET offset={angle_offset:+.1f}, -> READY")
                display_angle(oled, angle, label="SET")
                time.sleep_ms(500)
                state = STATE_READY
                last_display = time.ticks_ms()

        time.sleep_ms(10)  # yield to allow REPL interrupt


main()
