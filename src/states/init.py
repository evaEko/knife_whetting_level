import time
import ctx
from machine import I2C, Pin
from config import SDA_IMU, SCL_IMU, SDA_OLED, SCK_OLED, BTN_LOW, BTN_TOP, BNO085_ADDR, OLED_ADDR, ANGLE_FORMAT, LOAD_TARGET_ANGLE_FROM_EEPROM
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
        ctx.oled.fill(0)
        ctx.oled.show()
        print("OLED OK")
    except Exception as e:
        print(f"OLED ERROR: {e}")

    try:
        ctx.btn_low = Button(BTN_LOW)
        ctx.btn_top = Button(BTN_TOP)
        print("BTN OK")
    except Exception as e:
        print(f"BTN ERROR: {e}")

    if ctx.oled:
        pct = read_battery_pct()
        display_battery(ctx.oled, pct)
        if pct is None:
            while True:
                time.sleep_ms(500)
                pct = read_battery_pct()
                if pct is not None:
                    display_battery(ctx.oled, pct)
                    break
                if ((ctx.btn_low and ctx.btn_low.is_pressed()) or
                        (ctx.btn_top and ctx.btn_top.is_pressed())):
                    break

    try:
        ctx.imu = BNO085(i2c_imu, addr=BNO085_ADDR)
        ctx.imu.enable_rotation_vector(interval_ms=10)
        print("IMU OK")
    except Exception as e:
        print(f"IMU ERROR: {e}")

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
    print(f"ctx.board_offset set to: {ctx.board_offset}")
    ctx.load_settings(load_target_angle=LOAD_TARGET_ANGLE_FROM_EEPROM)
    ctx.angle_format = ctx.get_angle_format(ANGLE_FORMAT)

    if ctx.oled and pct is not None:
        time.sleep_ms(1500)
