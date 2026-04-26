oled    = None
imu     = None
btn_low = None
btn_top = None

board_offset      = 0.0  # persistent sensor mounting correction (saved to flash)
calibrated_offset = 0.0  # raw IMU angle at calibration point (display zero)
target_angle      = 0.0  # selected preset angle — display shows this value when correct
smooth_angle      = 0.0  # displayed value: (raw_angle - board_offset) - calibrated_offset
raw_angle         = 0.0
angle_format      = "1d_half"  # one of: 2d, 1d, 1d_half
angle_settings    = []   # list of (knife_id, angle) loaded from angles.csv


def save_settings():
    import ctx
    try:
        with open('settings.txt', 'w') as f:
            f.write(f"{ctx.calibrated_offset}\n{ctx.target_angle}\n")
    except Exception as e:
        print(f"Settings save error: {e}")


def load_settings():
    import ctx
    try:
        with open('settings.txt') as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        if len(lines) >= 2:
            ctx.calibrated_offset = float(lines[0])
            ctx.target_angle = float(lines[1])
        print("Settings loaded")
    except Exception:
        print("No settings saved, using defaults")


def get_angle_format(default_format):
    try:
        with open('angle_format.txt') as f:
            fmt = f.read().strip()
        if fmt in ("2d", "1d", "1d_half"):
            print(f"Angle format loaded: {fmt}")
            return fmt
    except Exception:
        pass
    print(f"No angle format saved, using default: {default_format}")
    return default_format


def store_angle_format_to_eeprom(fmt):
    try:
        with open('angle_format.txt', 'w') as f:
            f.write(fmt)
        print(f"-> ANGLE FORMAT saved: {fmt}")
    except Exception as e:
        print(f"Angle format save error: {e}")
