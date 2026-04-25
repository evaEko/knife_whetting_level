import time
import ctx
from machine import I2C, Pin
from config import SDA_IMU, SCL_IMU, SDA_OLED, SCK_OLED, BTN_LOW, BTN_TOP, BNO085_ADDR, OLED_ADDR
from drivers.ssd1306 import SSD1306
from drivers.bno085 import BNO085
from drivers.button import Button
from drivers.battery import read_battery_pct
from drivers.oled import display_battery
from states.level import get_board_level


def init():
    i2c_oled = I2C(1, sda=Pin(SDA_OLED), scl=Pin(SCK_OLED), freq=400000)
    i2c_imu  = I2C(0, sda=Pin(SDA_IMU),  scl=Pin(SCL_IMU),  freq=400000)

    try:
        ctx.oled = SSD1306(i2c_oled, addr=OLED_ADDR)
        print("OLED OK")
    except Exception as e:
        print(f"OLED ERROR: {e}")

    try:
        ctx.imu = BNO085(i2c_imu, addr=BNO085_ADDR)
        ctx.imu.enable_rotation_vector(interval_ms=10)
        print("IMU OK")
    except Exception as e:
        print(f"IMU ERROR: {e}")

    try:
        ctx.btn_low = Button(BTN_LOW)
        ctx.btn_top = Button(BTN_TOP)
        print("BTN OK")
    except Exception as e:
        print(f"BTN ERROR: {e}")

    try:
        with open('angles.csv') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(',')
                if len(parts) == 2:
                    ctx.angle_settings.append((parts[0].strip(), float(parts[1].strip())))
        print(f"Loaded {len(ctx.angle_settings)} angle presets")
    except Exception as e:
        print(f"angles.csv error: {e}")

    ctx.board_offset = get_board_level()

    if ctx.oled:
        display_battery(ctx.oled, read_battery_pct())
        time.sleep_ms(1500)
