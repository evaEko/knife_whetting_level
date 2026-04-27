import time
from machine import I2C, Pin
import ctx
from config import SDA_OLED, SCK_OLED, OLED_ADDR
from drivers.ssd1306 import SSD1306
from drivers.oled import draw_boot_knife
from states.init import init

try:
    ctx.oled = SSD1306(I2C(1, sda=Pin(SDA_OLED), scl=Pin(SCK_OLED), freq=400000), addr=OLED_ADDR)
    draw_boot_knife(ctx.oled)
except Exception:
    pass

time.sleep_ms(1000)

from states.measure import measure
from states.calibration import calibrate
from states.select_angle import select_angle
from states.select_angle_format import select_angle_format
from states.flash import flash
from states.level import level


def main():
    try:
        init()
    except Exception as e:
        print(f"INIT CRASH: {e}")
        return
    while True:
        event = measure()
        if event == ('short', 'low'):
            calibrate()
        elif event == ('short', 'top'):
            select_angle()
        elif event == ('long', 'top'):
            select_angle_format()
        elif event == ('short', 'both'):
            flash()
        elif event == ('long', 'low'):
            level()


main()
