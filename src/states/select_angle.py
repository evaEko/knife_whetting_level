import time
import ctx

_index = 0


def _show(name, angle):
    ctx.oled.fill(0)
    ctx.oled.text(name[:16], 0, 0, 1)
    ctx.oled.large_text(f"{angle:.0f}", 0, 12, scale=2)
    ctx.oled.text("low=set  top=next", 0, 32, 1)
    ctx.oled.show()


def _show_clear():
    ctx.oled.fill(0)
    ctx.oled.text("Clear angle", 0, 4, 1)
    ctx.oled.text("low=clear top=next", 0, 32, 1)
    ctx.oled.show()


def select_angle():
    global _index
    if not ctx.oled or not ctx.angle_settings:
        return

    total = len(ctx.angle_settings) + 1  # +1 for Clear option
    if _index >= total:
        _index = 0

    ctx.oled.invert(False)
    if _index < len(ctx.angle_settings):
        _show(*ctx.angle_settings[_index])
    else:
        _show_clear()

    while True:
        ev_low = ctx.btn_low.update() if ctx.btn_low else None
        ev_top = ctx.btn_top.update() if ctx.btn_top else None

        if ev_top == 'short':
            _index = (_index + 1) % total
            if _index < len(ctx.angle_settings):
                _show(*ctx.angle_settings[_index])
            else:
                _show_clear()

        elif ev_low == 'short':
            if _index < len(ctx.angle_settings):
                name, angle = ctx.angle_settings[_index]
                ctx.target_angle = angle
                ctx.smooth_angle = 0.0
                ctx.save_settings()
                print(f"-> PRESET '{name}' {angle}°")
                ctx.oled.fill(0)
                ctx.oled.text("SET", 24, 4, 1)
                ctx.oled.large_text(f"{angle:.0f}", 0, 16, scale=2)
                ctx.oled.show()
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
