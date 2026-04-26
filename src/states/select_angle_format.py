import time
import ctx

_index = 0
_OPTIONS = [
    ("2 decimals", "2d", "+12.34"),
    ("1 decimal", "1d", "+12.3"),
    ("0/5 steps", "1d_half", "+12.5"),
]


def _show(name, sample):
    ctx.oled.fill(0)
    ctx.oled.text("Angle format", 0, 0, 1)
    ctx.oled.text(name[:16], 0, 10, 1)
    ctx.oled.text(sample, 0, 22, 1)
    ctx.oled.text("low=set top=next", 0, 32, 1)
    ctx.oled.show()


def select_angle_format():
    global _index
    if not ctx.oled:
        return

    for i, (_, key, _) in enumerate(_OPTIONS):
        if key == ctx.angle_format:
            _index = i
            break

    ctx.oled.invert(False)
    _show(_OPTIONS[_index][0], _OPTIONS[_index][2])

    while True:
        ev_low = ctx.btn_low.update() if ctx.btn_low else None
        ev_top = ctx.btn_top.update() if ctx.btn_top else None

        if ev_top == 'short':
            _index = (_index + 1) % len(_OPTIONS)
            _show(_OPTIONS[_index][0], _OPTIONS[_index][2])

        elif ev_low == 'short':
            name, key, sample = _OPTIONS[_index]
            ctx.angle_format = key
            ctx.save_settings()
            print(f"-> ANGLE FORMAT {key}")
            ctx.oled.fill(0)
            ctx.oled.text("FORMAT SET", 0, 4, 1)
            ctx.oled.text(name[:16], 0, 16, 1)
            ctx.oled.text(sample, 0, 26, 1)
            ctx.oled.show()
            time.sleep_ms(700)
            return

        elif ev_low == 'long' or ev_top == 'long':
            return

        time.sleep_ms(10)
