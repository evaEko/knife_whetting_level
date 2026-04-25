import time
import ctx


def get_board_level():
    try:
        with open('board_offset.txt') as f:
            value = float(f.read().strip())
        print(f"Board level loaded: {value:+.2f}")
        return value
    except Exception:
        print("No board level saved, using 0.0")
        return 0.0


def store_level_to_eeprom(angle):
    try:
        with open('board_offset.txt', 'w') as f:
            f.write(str(angle))
        print(f"-> BOARD OFFSET saved: {angle:+.2f}")
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

    while ctx.btn_low and ctx.btn_low.is_pressed():
        time.sleep_ms(10)
    time.sleep_ms(50)

    while True:
        if ctx.imu:
            try:
                ctx.imu.update()
                ctx.raw_angle = ctx.imu.get_pitch()
            except OSError:
                pass

        if ctx.btn_low and ctx.btn_low.is_pressed():
            time.sleep_ms(50)
            if ctx.btn_low.is_pressed():
                start = time.ticks_ms()
                while ctx.btn_low.is_pressed():
                    time.sleep_ms(10)
                duration = time.ticks_diff(time.ticks_ms(), start)
                if duration >= 800:
                    store_level_to_eeprom(0.0)
                    ctx.oled.fill(0)
                    ctx.oled.text("BL reset", 16, 4, 1)
                    ctx.oled.text("Reboot!", 4, 20, 1)
                    ctx.oled.show()
                else:
                    store_level_to_eeprom(ctx.raw_angle)
                    ctx.oled.fill(0)
                    ctx.oled.text("Reboot!", 16, 12, 1)
                    ctx.oled.show()
                time.sleep_ms(2000)
                return

        time.sleep_ms(10)
