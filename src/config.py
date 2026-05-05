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
DEVIATION_THRESHOLD = 1   # degrees

# How long the button must be held to count as a long press
LONG_PRESS_MS = 1000  # ms

# Display smoothing — low-pass filter on the displayed angle.
# Higher = smoother reading, slower to respond to angle changes.
#   0.3 — very reactive, good for learning (see every wobble)
#   0.5 — balanced
#   0.7 — smooth, good default for most users
#   0.9 — near-frozen display, suited to experienced sharpeners
#          who hold a consistent angle and want a stable reading
SMOOTHING = 0.7

# Angle display format:
#   "2d"      — two decimal places  (e.g. +12.34°)
#   "1d"      — one decimal place   (e.g. +12.3°)
#   "1d_half" — one decimal place, rounded to nearest 0.5  (e.g. +12.5°)
ANGLE_FORMAT = "1d_half"

# Whether to restore the last selected preset angle from persisted settings
# at boot. True keeps the current behavior; False starts with no preset selected.
LOAD_TARGET_ANGLE_FROM_EEPROM = True

# Measuring screen overlays — show preset name (top) and target angle (bottom)
# when a preset is active. Set either to False to hide that element.
SHOW_PRESET_NAME   = True
SHOW_TARGET_ANGLE  = False

# How often the measuring screen redraws (ms). Lower = more responsive, more I2C traffic.
DISPLAY_INTERVAL_MS = 40

# Enable Bluetooth Low Energy UART service on boot.
BLE_ENABLED = True 
