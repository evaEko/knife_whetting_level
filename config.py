# Pin configuration  (notation: first digit = port, last two = pin)
SDA_IMU  = 38   
SCL_IMU  = 36   
SDA_OLED = 6    
SCK_OLED = 8    
BTN_CAL  = 43   # P1.11

# I2C addresses
BNO085_ADDR = 0x4B
OLED_ADDR   = 0x3C

# Thresholds
DEVIATION_THRESHOLD = 2.0   # degrees
LONG_PRESS_MS       = 1000  # ms to count as long press

# Output smoothing (low-pass on displayed angle)
SMOOTHING = 0.15  # 0.0 = no smoothing, higher = more smooth (max ~0.5)
