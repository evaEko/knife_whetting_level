def display_angle(oled, angle, label=None, fmt="1d_half"):
    oled.fill(0)
    if fmt == "2d":
        if -10.0 < angle < 10.0:
            text = f" {angle:+.2f}"
        else:
            text = f"{angle:+.2f}"
        # Keep a simple fixed layout that still fits on the 72px display.
        # Digits/sign stay readable, while '.' is only slightly tighter.
        advances = []
        for ch in text:
            if ch == ' ':
                advances.append(5)
            elif ch == '.':
                advances.append(4)
            else:
                advances.append(6)
        # Total width stays within 72px at scale=2 for both padded and unpadded forms.
        x = 0
        y = 4 if label else 12
        oled.large_text_adv(text, x, y, scale=2, advances=advances)
        if label:
            oled.text(label, 0, 24, 1)
        oled.show()
        return
    elif fmt == "1d":
        angle = round(angle, 1)
        text = f"{angle:+.1f}"
    else:  # "1d_half"
        angle = round(angle * 2) / 2
        text = f"{angle:+.1f}"
    # pad single-digit angles so the decimal point stays at a fixed x position
    if fmt != "2d" and -10.0 < angle < 10.0:
        text = " " + text
    x = 0
    y = 4 if label else 12
    # char_pitch=7: each char advances 14px at scale=2 (vs 16px default)
    # → 5 chars = 70px, fits the 72px-wide display without clipping
    oled.large_text(text, x, y, scale=2, char_pitch=7)
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
    if pct is None:
        oled.text("Turn on", 8, 0, 1)
        oled.text("to charge", 0, 10, 1)
        oled.text("click=", 0, 22, 1)
        oled.text("bypass", 0, 32, 1)
    else:
        oled.text("BAT", (72 - 24) // 2, 2, 1)
        pct_str = f"{pct}%"
        pw = len(pct_str) * 16  # scale=2 → 16px per char
        oled.large_text(pct_str, (72 - pw) // 2, 14, scale=2)
        bx, by, bw, bh = 6, 33, 60, 5
        oled.fb.rect(bx, by, bw, bh, 1)
        filled = int(bw * pct / 100)
        if filled > 0:
            oled.fb.fill_rect(bx, by, filled, bh, 1)
    oled.show()
