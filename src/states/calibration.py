import time
import ctx
from drivers.oled import display_angle


def _draw_calibration_angle(angle):
    if ctx.angle_format == "2d":
        if -10.0 < angle < 10.0:
            text = f" {angle:+.2f}"
        else:
            text = f"{angle:+.2f}"
        x = -2
        y = 12
        ctx.oled.large_text(text, x, y, scale=2, char_pitch=6)
        return

    if ctx.angle_format == "1d":
        angle = round(angle, 1)
        text = f"{angle:+.1f}"
    else:
        angle = round(angle * 2) / 2
        text = f"{angle:+.1f}"

    if -10.0 < angle < 10.0:
        text = " " + text
    ctx.oled.large_text(text, 0, 12, scale=2, char_pitch=7)


def _show_calibration(angle):
    ctx.oled.fill(0)
    # 72px width is too tight for the full strings; use compact hints.
    ctx.oled.text("top=esc", 0, 0, 1)
    ctx.oled.text("low=ok", 8, 32, 1)
    _draw_calibration_angle(angle)
    ctx.oled.show()


def _update_calibration_angle(angle):
    # Clear only the angle band so the static hints do not flicker.
    ctx.oled.fb.fill_rect(0, 12, 72, 16, 0)
    _draw_calibration_angle(angle)
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

        _update_calibration_angle(ctx.smooth_angle)

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
