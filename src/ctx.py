oled    = None
imu     = None
btn_low = None
btn_top = None

board_offset      = 0.0  # persistent sensor mounting correction (saved to flash)
calibrated_offset = 0.0  # raw IMU angle at calibration point (display zero)
target_angle      = 0.0  # selected preset angle — display shows this value when correct
smooth_angle      = 0.0  # displayed value: (raw_angle - board_offset) - calibrated_offset
raw_angle         = 0.0
angle_settings    = []   # list of (knife_id, angle) loaded from angles.csv


def save_settings():
    import ctx
    try:
        with open('settings.txt', 'w') as f:
            f.write(f"{ctx.calibrated_offset}\n{ctx.target_angle}\n")
    except Exception as e:
        print(f"Settings save error: {e}")
