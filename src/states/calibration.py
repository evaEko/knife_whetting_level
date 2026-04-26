import time
import ctx
from drivers.oled import display_angle


def _show_calibration(angle):
    display_angle(ctx.oled, angle)
    # 72px width is too tight for the full strings; use compact hints.
    ctx.oled.text("top=esc", 0, 0, 1)
    ctx.oled.text("low=ok", 8, 32, 1)
    ctx.oled.show()


def calibrate():
    ctx.oled.invert(False)
    _show_calibration(ctx.smooth_angle)

    while True:
        try:
            ctx.imu.update()
            ctx.raw_angle = ctx.imu.get_pitch()
            angle = ctx.raw_angle - ctx.board_offset - ctx.calibrated_offset
            while angle > 180.0:  angle -= 360.0
            while angle < -180.0: angle += 360.0
            ctx.smooth_angle = ctx.smooth_angle * 0.15 + angle * 0.85
        except OSError:
            time.sleep_ms(5)
            continue

        _show_calibration(ctx.smooth_angle)

        ev_low = ctx.btn_low.update() if ctx.btn_low else None
        ev_top = ctx.btn_top.update() if ctx.btn_top else None

        if ev_low == 'short':
            ctx.calibrated_offset = ctx.raw_angle - ctx.board_offset
            ctx.smooth_angle = 0.0
            print(f"-> CAL calibrated_offset={ctx.calibrated_offset:+.1f}")
            display_angle(ctx.oled, 0.0, label="SET")
            time.sleep_ms(500)
            return

        if ev_top == 'short':
            print("-> CAL canceled")
            return

        time.sleep_ms(10)
