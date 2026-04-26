# Pin configuration (notation: first digit = port, last two = pin)
SDA_IMU  = 38   # I2C data  — BNO085 IMU
SCL_IMU  = 36   # I2C clock — BNO085 IMU
SDA_OLED = 6    # I2C data  — SSD1306 OLED display
SCK_OLED = 8    # I2C clock — SSD1306 OLED display
BTN_LOW  = 43   # Low button (P1.11) — calibration / power off
BTN_TOP  = 45   # Top button (P1.13) — preset cycling

# I2C addresses
BNO085_ADDR = 0x4B  # BNO085 default address (ADR pin low)
OLED_ADDR   = 0x3C  # SSD1306 default address

# Angle deviation threshold — how many degrees off your target before the
# display inverts to warn you
DEVIATION_THRESHOLD = 2.0   # degrees

# How long the button must be held to count as a long press
LONG_PRESS_MS = 1000  # ms

# Display smoothing — low-pass filter on the displayed angle.
# 0.0 = raw/no smoothing, higher = smoother but slower to respond.
# Keep below 0.5 to avoid excessive lag during fast movements.
SMOOTHING = 0.15

# Angle display format:
#   "2d"      — two decimal places  (e.g. +12.34°)
#   "1d"      — one decimal place   (e.g. +12.3°)
#   "1d_half" — one decimal place, rounded to nearest 0.5  (e.g. +12.5°)
ANGLE_FORMAT = "1d_half"

# Whether to restore the last selected preset angle from persisted settings
# at boot. True keeps the current behavior; False starts with no preset selected.
LOAD_TARGET_ANGLE_FROM_EEPROM = True 
