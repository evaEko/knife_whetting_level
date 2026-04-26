import time
import ctx
from config import SMOOTHING
from drivers.oled import display_angle

_index = 0

CUSTOM = 0  # first slot


def _show(name, angle):
    ctx.oled.fill(0)
    ctx.oled.text(name[:16], 0, 0, 1)
    ctx.oled.large_text(f"{angle:.0f}", 0, 12, scale=2)
    ctx.oled.text("low=set  top=next", 0, 32, 1)
    ctx.oled.show()


def _show_custom():
    ctx.oled.fill(0)
    ctx.oled.text("Custom angle", 0, 4, 1)
    ctx.oled.text("low=set", 0, 20, 1)
    ctx.oled.show()


def _show_clear():
    ctx.oled.fill(0)
    ctx.oled.text("Clear angle", 0, 4, 1)
    ctx.oled.text("low=clear top=next", 0, 32, 1)
    ctx.oled.show()


def _display_item(index, n):
    if index == CUSTOM:
        _show_custom()
    elif index <= n:
        _show(*ctx.angle_settings[index - 1])
    else:
        _show_clear()


def select_angle():
    global _index
    if not ctx.oled or not ctx.angle_settings:
        return

    n = len(ctx.angle_settings)
    CLEAR = n + 1
    total = n + 2  # Custom + presets + Clear

    if _index >= total:
        _index = 0

    ctx.oled.invert(False)
    _display_item(_index, n)

    while True:
        ev_low = ctx.btn_low.update() if ctx.btn_low else None
        ev_top = ctx.btn_top.update() if ctx.btn_top else None

        if ev_top == 'short':
            _index = (_index + 1) % total
            _display_item(_index, n)

        elif ev_low == 'short':
            if _index == CUSTOM:
                ctx.oled.invert(False)
                last_display = 0
                while True:
                    if ctx.imu is not None:
                        try:
                            ctx.imu.update()
                            ctx.raw_angle = ctx.imu.get_pitch()
                            angle = ctx.raw_angle - ctx.board_offset - ctx.calibrated_offset
                            while angle > 180.0:  angle -= 360.0
                            while angle < -180.0: angle += 360.0
                            if abs(angle - ctx.smooth_angle) > 180.0:
                                ctx.smooth_angle = angle
                            else:
                                ctx.smooth_angle = SMOOTHING * ctx.smooth_angle + (1.0 - SMOOTHING) * angle
                        except OSError:
                            pass
                    now = time.ticks_ms()
                    if time.ticks_diff(now, last_display) >= 50:
                        last_display = now
                        display_angle(ctx.oled, ctx.smooth_angle, label="low=set", fmt=ctx.angle_format)
                    ev2_low = ctx.btn_low.update() if ctx.btn_low else None
                    ev2_top = ctx.btn_top.update() if ctx.btn_top else None
                    if ev2_low == 'short':
                        ctx.target_angle = ctx.smooth_angle
                        ctx.smooth_angle = 0.0
                        ctx.save_settings()
                        print(f"-> CUSTOM {ctx.target_angle:.2f}°")
                        ctx.oled.fill(0)
                        ctx.oled.text("SET", 24, 4, 1)
                        ctx.oled.show()
                        time.sleep_ms(1000)
                        return
                    elif ev2_top == 'short' or ev2_low == 'long' or ev2_top == 'long':
                        return
                    time.sleep_ms(10)
            elif _index < CLEAR:
                name, angle = ctx.angle_settings[_index - 1]
                ctx.target_angle = angle
                ctx.smooth_angle = 0.0
                ctx.save_settings()
                print(f"-> PRESET '{name}' {angle}°")
                ctx.oled.fill(0)
                ctx.oled.text("SET", 24, 4, 1)
                ctx.oled.large_text(f"{angle:.0f}", 0, 16, scale=2)
                ctx.oled.show()
                time.sleep_ms(1000)
                return
            else:
                ctx.target_angle = 0.0
                ctx.smooth_angle = 0.0
                ctx.save_settings()
                print("-> PRESET cleared")
                ctx.oled.fill(0)
                ctx.oled.text("Cleared", 12, 12, 1)
                ctx.oled.show()
                time.sleep_ms(1000)
                return

        elif ev_low == 'long' or ev_top == 'long':
            return

        time.sleep_ms(10)
