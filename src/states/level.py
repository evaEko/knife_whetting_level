import time
import ctx


def store_level_to_eeprom(angle):
    ctx.board_offset = ctx.board_offset + angle
    try:
        with open('board_offset.txt', 'w') as f:
            f.write(str(ctx.board_offset))
        print(f"-> BOARD OFFSET saved: {ctx.board_offset:+.2f}")
    except Exception as e:
        print(f"Save error: {e}")


def level():
    if not ctx.oled:
        return

    ctx.oled.invert(False)
    ctx.oled.fill(0)
    ctx.oled.text("Place on", 12, 4, 1)
    ctx.oled.text("straight", 12, 16, 1)
    ctx.oled.text("surface", 12, 28, 1)
    ctx.oled.show()

    # wait for button to be fully released
    while ctx.btn_low and ctx.btn_low.is_pressed():
        time.sleep_ms(10)
    time.sleep_ms(50)

    while True:
        if ctx.btn_low and ctx.btn_low.is_pressed():
            time.sleep_ms(50)  # debounce
            if ctx.btn_low.is_pressed():
                while ctx.btn_low.is_pressed():
                    time.sleep_ms(10)
                store_level_to_eeprom(ctx.raw_angle)
                ctx.oled.fill(0)
                ctx.oled.text("Saved!", 20, 12, 1)
                ctx.oled.show()
                time.sleep_ms(1000)
                return

        time.sleep_ms(10)
