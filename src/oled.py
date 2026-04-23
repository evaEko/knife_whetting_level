def display_angle(oled, angle, label=None):
    oled.fill(0)
    angle = round(angle * 2) / 2
    text = f"{angle:+.1f}"
    x = 0
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


def display_battery(oled, pct):
    oled.fill(0)
    oled.text("BAT", (72 - 24) // 2, 2, 1)
    if pct is None:
        oled.text("--", (72 - 16) // 2, 16, 1)
    else:
        pct_str = f"{pct}%"
        pw = len(pct_str) * 16  # scale=2 → 16px per char
        oled.large_text(pct_str, (72 - pw) // 2, 14, scale=2)
        bx, by, bw, bh = 6, 33, 60, 5
        oled.fb.rect(bx, by, bw, bh, 1)
        filled = int(bw * pct / 100)
        if filled > 0:
            oled.fb.fill_rect(bx, by, filled, bh, 1)
    oled.show()
