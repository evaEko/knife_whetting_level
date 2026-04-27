import ctx
from machine import I2C, Pin
from config import SDA_OLED, SCK_OLED, OLED_ADDR
from drivers.ssd1306 import SSD1306


def init_oled():
    if ctx.oled is not None:
        return
    try:
        ctx.oled = SSD1306(I2C(1, sda=Pin(SDA_OLED), scl=Pin(SCK_OLED), freq=400000), addr=OLED_ADDR)
        print("OLED OK")
    except Exception as e:
        print(f"OLED ERROR: {e}")
