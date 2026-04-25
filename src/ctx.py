oled    = None
imu     = None
btn_low = None
btn_top = None

calibrated_offset = 0.0  # raw IMU angle at calibration point (display zero)
target_angle      = 0.0  # selected preset angle — display shows this value when correct
smooth_angle      = 0.0  # displayed value: raw_angle - calibrated_offset
raw_angle         = 0.0
angle_settings    = []   # list of (knife_id, angle) loaded from angles.csv
