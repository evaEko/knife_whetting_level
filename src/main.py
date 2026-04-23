import machine
import time
from machine import I2C, Pin

from config import (
    SDA_IMU, SCL_IMU, SDA_OLED, SCK_OLED, BTN_CAL,
    BNO085_ADDR, OLED_ADDR, SMOOTHING,
)
from drivers.bno085 import BNO085
from drivers.ssd1306 import SSD1306
from drivers.button import Button
from drivers.battery import read_battery_pct
from drivers.oled import display_battery
from states import STATE_READY, STATE_CALIBRATION
import states.ready as state_ready
import states.calibration as state_calibration

IDLE_TIMEOUT       = 60_000  # ms of no movement before slowing IMU
MOVEMENT_THRESHOLD = 0.5     # degrees delta to count as movement
DISPLAY_INTERVAL   = 50      # ms between display refreshes
LOG_INTERVAL       = 500     # ms between serial log messages


def main():
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

    display_battery(oled, read_battery_pct())
    time.sleep_ms(1500)

    ctx = {
        'state':        STATE_READY,
        'angle_offset': 0.0,
        'smooth_angle': 0.0,
    }

    imu_idle       = False
    last_movement  = time.ticks_ms()
    idle_ref_angle = 0.0
    last_display   = time.ticks_ms()
    last_log       = time.ticks_ms()
    loop_count     = 0

    print("Entering main loop, state=READY")

    # ── Main loop ─────────────────────────────────────────────────────────────
    while True:
        try:
            imu.update()
            raw_angle = imu.get_pitch()
            angle = raw_angle - ctx['angle_offset']
            while angle > 180.0:
                angle -= 360.0
            while angle < -180.0:
                angle += 360.0
            if abs(angle - ctx['smooth_angle']) > 180.0:
                ctx['smooth_angle'] = angle
            else:
                ctx['smooth_angle'] = SMOOTHING * ctx['smooth_angle'] + (1.0 - SMOOTHING) * angle
        except OSError:
            time.sleep_ms(5)
            continue

        event = btn.update()
        loop_count += 1

        # ── Idle / wake detection ─────────────────────────────────────────────
        now = time.ticks_ms()
        if abs(ctx['smooth_angle'] - idle_ref_angle) >= MOVEMENT_THRESHOLD:
            idle_ref_angle = ctx['smooth_angle']
            last_movement = now
            if imu_idle:
                imu.set_report_interval(10)
                imu_idle = False
                print("-> IMU WAKE")
        elif not imu_idle and time.ticks_diff(now, last_movement) >= IDLE_TIMEOUT:
            imu.set_report_interval(1000)
            imu_idle = True
            print("-> IMU IDLE")

        update_display = time.ticks_diff(now, last_display) >= DISPLAY_INTERVAL
        if update_display:
            last_display = now

        if time.ticks_diff(now, last_log) >= LOG_INTERVAL:
            print(f"s={ctx['state']} raw={raw_angle:+.1f} a={angle:+.1f} sm={ctx['smooth_angle']:+.1f} off={ctx['angle_offset']:+.1f} loops={loop_count}")
            loop_count = 0
            last_log = now

        if event is not None:
            print(f"BTN EVENT: {event} (state={ctx['state']})")

        # ── Long press: power off from any state ──────────────────────────────
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
            wake_pending = [False]
            def on_btn_press(pin):
                wake_pending[0] = True
            btn.pin.irq(trigger=Pin.IRQ_FALLING, handler=on_btn_press)
            while True:
                machine.idle()
                if wake_pending[0] or btn.is_pressed():
                    wake_pending[0] = False
                    start = time.ticks_ms()
                    while btn.is_pressed():
                        time.sleep_ms(10)
                    if time.ticks_diff(time.ticks_ms(), start) >= 30:
                        btn.pin.irq(handler=None)
                        print("-> WAKE UP")
                        machine.reset()

        # ── State dispatch ────────────────────────────────────────────────────
        if ctx['state'] == STATE_READY:
            state_ready.run(ctx, oled, event, update_display)
        elif ctx['state'] == STATE_CALIBRATION:
            state_calibration.run(ctx, oled, raw_angle, event, update_display)

        time.sleep_ms(10)


main()
