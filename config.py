# Pin configuration  (notation: first digit = port, last two = pin)
SDA_IMU  = 36   # P1.04 -> pin 104
SCL_IMU  = 38   # P1.06 -> pin 106
SDA_OLED = 6    # P0.06 -> pin 006
SCK_OLED = 8    # P0.08 -> pin 008
BTN_CAL  = 11   # P0.11 -> pin 011 (D7)

# I2C addresses
BNO085_ADDR = 0x4B
OLED_ADDR   = 0x3C

# Thresholds
DEVIATION_THRESHOLD = 3.0   # degrees
LONG_PRESS_MS       = 1000  # ms to count as long press

# Output smoothing (low-pass on displayed angle)
SMOOTHING = 0.15  # 0.0 = no smoothing, higher = more smooth (max ~0.5)
