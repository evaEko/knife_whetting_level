import time
import ctx


_index = 0


def _show(name, angle):
    ctx.oled.fill(0)
    ctx.oled.text(name[:16], 0, 0, 1)
    ctx.oled.large_text(f"{angle:.0f}", 0, 12, scale=2)
    ctx.oled.text("low=set  top=next", 0, 32, 1)
    ctx.oled.show()


def select_angle():
    global _index
    if not ctx.oled or not ctx.angle_settings:
        return

    if _index >= len(ctx.angle_settings):
        _index = 0

    ctx.oled.invert(False)
    _show(*ctx.angle_settings[_index])

    while True:
        ev_low = ctx.btn_low.update() if ctx.btn_low else None
        ev_top = ctx.btn_top.update() if ctx.btn_top else None

        if ev_top == 'short':
            _index = (_index + 1) % len(ctx.angle_settings)
            _show(*ctx.angle_settings[_index])

        elif ev_low == 'short':
            name, angle = ctx.angle_settings[_index]
            ctx.angle_offset = angle
            ctx.smooth_angle = 0.0
            print(f"-> PRESET '{name}' {angle}°")
            ctx.oled.fill(0)
            ctx.oled.text("SET", 24, 4, 1)
            ctx.oled.large_text(f"{angle:.0f}", 0, 16, scale=2)
            ctx.oled.show()
            time.sleep_ms(1000)
            return

        elif ev_low == 'long' or ev_top == 'long':
            return

        time.sleep_ms(10)
