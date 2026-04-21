import machine
import time
import math
from machine import I2C, Pin

from config import (
    SDA_IMU, SCL_IMU, SDA_OLED, SCK_OLED, BTN_CAL,
    BNO085_ADDR, OLED_ADDR,
    DEVIATION_THRESHOLD, LONG_PRESS_MS, SMOOTHING
)
from bno085 import BNO085
from ssd1306 import SSD1306

# ── States ────────────────────────────────────────────────────────────────────
STATE_INIT        = "INIT"
STATE_READY       = "READY"
STATE_CALIBRATION = "CALIBRATION"


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

    # ── INIT ──────────────────────────────────────────────────────────────────
    try:
        i2c_imu  = I2C(0, sda=Pin(SDA_IMU),  scl=Pin(SCL_IMU),  freq=400000)
        i2c_oled = I2C(1, sda=Pin(SDA_OLED), scl=Pin(SCK_OLED), freq=400000)
        oled     = SSD1306(i2c_oled, addr=OLED_ADDR)

        oled.fill(0)
        oled.text("BNO085...", 4, 12, 1)
        oled.show()

        imu = BNO085(i2c_imu, addr=BNO085_ADDR)
        imu.enable_rotation_vector(interval_ms=10)
        btn = Button(BTN_CAL)
    except Exception as e:
        print(f"INIT ERROR: {e}")
        return

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
        try:
            imu.update()
            raw_angle = imu.get_roll()
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
            imu.suspend()
            while True:
                machine.lightsleep()
                if btn.is_pressed():
                    start = time.ticks_ms()
                    while btn.is_pressed():
                        time.sleep_ms(10)
                    if time.ticks_diff(time.ticks_ms(), start) >= LONG_PRESS_MS:
                        print("-> WAKE UP")
                        machine.reset()

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
