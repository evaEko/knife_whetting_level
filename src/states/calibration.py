import time
import ctx
from drivers.oled import display_angle


def calibrate():
    ctx.oled.invert(False)
    display_angle(ctx.oled, ctx.smooth_angle, label="CAL")

    while True:
        try:
            ctx.imu.update()
            ctx.raw_angle = ctx.imu.get_pitch()
            angle = ctx.raw_angle - ctx.calibrated_offset
            while angle > 180.0:  angle -= 360.0
            while angle < -180.0: angle += 360.0
            ctx.smooth_angle = ctx.smooth_angle * 0.15 + angle * 0.85
        except OSError:
            time.sleep_ms(5)
            continue

        display_angle(ctx.oled, ctx.smooth_angle, label="CAL")

        event = ctx.btn_low.update()
        if event == 'short':
            ctx.calibrated_offset = ctx.raw_angle
            ctx.smooth_angle = 0.0
            print(f"-> CAL calibrated_offset={ctx.calibrated_offset:+.1f}")
            display_angle(ctx.oled, 0.0, label="SET")
            time.sleep_ms(500)
            return

        time.sleep_ms(10)
