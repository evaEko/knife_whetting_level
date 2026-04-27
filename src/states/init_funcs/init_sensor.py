import ctx
from machine import I2C, Pin
from config import SDA_IMU, SCL_IMU, BNO085_ADDR
from drivers.bno085 import BNO085


def init_sensor():
    try:
        ctx.imu = BNO085(I2C(0, sda=Pin(SDA_IMU), scl=Pin(SCL_IMU), freq=400000), addr=BNO085_ADDR)
        ctx.imu.enable_rotation_vector(interval_ms=10)
        print("IMU OK")
    except Exception as e:
        print(f"IMU ERROR: {e}")
