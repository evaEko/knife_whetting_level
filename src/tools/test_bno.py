import time
from machine import I2C, Pin
from config import SDA_IMU, SCL_IMU, BNO085_ADDR
from bno085 import BNO085

i2c = I2C(0, sda=Pin(SDA_IMU), scl=Pin(SCL_IMU), freq=400000)
print("I2C scan:", [hex(a) for a in i2c.scan()])

imu = BNO085(i2c, addr=BNO085_ADDR)
imu.enable_rotation_vector(interval_ms=10)
print("BNO085 OK, rotation vector enabled")

while True:
    if imu.update():
        roll = imu.get_roll()
        w, x, y, z = imu._quat
        print(f"roll={roll:+.1f}  quat=({w:.3f}, {x:.3f}, {y:.3f}, {z:.3f})")
    time.sleep_ms(50)
