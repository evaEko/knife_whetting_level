# Pin configuration  (notation: first digit = port, last two = pin)
SDA_BMI  = 36   # P1.04 -> pin 104
SCL_BMI  = 38   # P1.06 -> pin 106
SDA_OLED = 6    # P0.06 -> pin 006
SCK_OLED = 8    # P0.08 -> pin 008
BTN_CAL  = 45   # P1.13 -> pin 113 (D15)

# I2C addresses
BMI160_ADDR = 0x68
OLED_ADDR   = 0x3C

# Thresholds
DEVIATION_THRESHOLD = 2.0   # degrees
LONG_PRESS_MS       = 1000  # ms to count as long press

# Complementary filter
ALPHA = 0.96  # gyro weight; 1-ALPHA = accel weight

# Output smoothing (low-pass on displayed angle)
SMOOTHING = 0.3  # 0.0 = no smoothing, higher = more smooth (max ~0.5)
