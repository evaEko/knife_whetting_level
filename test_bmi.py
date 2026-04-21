import time
from machine import I2C, Pin
from config import SDA_BMI, SCL_BMI, BMI160_ADDR
from bmi160 import BMI160

i2c = I2C(0, sda=Pin(SDA_BMI), scl=Pin(SCL_BMI), freq=400000)
print("I2C scan:", [hex(a) for a in i2c.scan()])

bmi = BMI160(i2c, addr=BMI160_ADDR)
print("BMI160 OK")

while True:
    try:
        ax, ay, az, gx, gy, gz = bmi.read_all()
        print(f"ax={ax:+.3f} ay={ay:+.3f} az={az:+.3f} gx={gx:+.1f} gy={gy:+.1f} gz={gz:+.1f}")
    except OSError as e:
        print(f"I2C error: {e}")
    time.sleep_ms(500)
