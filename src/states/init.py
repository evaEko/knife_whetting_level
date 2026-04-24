import time
import ctx
from machine import I2C, Pin
from config import SDA_IMU, SCL_IMU, SDA_OLED, SCK_OLED, BTN_CAL, BNO085_ADDR, OLED_ADDR
from drivers.ssd1306 import SSD1306
from drivers.bno085 import BNO085
from drivers.button import Button
from drivers.battery import read_battery_pct
from drivers.oled import display_battery, display_error


def init():
    i2c_oled = I2C(1, sda=Pin(SDA_OLED), scl=Pin(SCK_OLED), freq=400000)
    i2c_imu  = I2C(0, sda=Pin(SDA_IMU),  scl=Pin(SCL_IMU),  freq=400000)

    try:
        ctx.oled = SSD1306(i2c_oled, addr=OLED_ADDR)
    except Exception as e:
        print(f"OLED ERROR: {e}")
        raise

    try:
        ctx.oled.fill(0)
        ctx.oled.text("Checking IMU...", 0, 12, 1)
        ctx.oled.show()
        ctx.imu = BNO085(i2c_imu, addr=BNO085_ADDR)
        ctx.imu.enable_rotation_vector(interval_ms=10)
    except Exception as e:
        display_error(ctx.oled, "IMU fail")
        print(f"IMU ERROR: {e}")
        raise

    try:
        ctx.btn = Button(BTN_CAL)
    except Exception as e:
        display_error(ctx.oled, "BTN fail")
        print(f"BTN ERROR: {e}")
        raise

    display_battery(ctx.oled, read_battery_pct())
    time.sleep_ms(1500)
