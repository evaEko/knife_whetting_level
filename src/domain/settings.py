class Settings:
    def __init__(self, default_angle_format="1d_half", load_target_angle=True):
        self.calibrated_offset  = 0.0
        self.target_angle       = 0.0
        self.angle_format       = default_angle_format
        self.board_offset        = 0.0
        self.surface_normal      = None  # (nx, ny, nz) or None
        self.calibrated_gravity  = None  # (gx, gy, gz) gravity unit vector at calibration position
        self._load_target_angle  = load_target_angle

    def load(self):
        try:
            with open('settings.txt') as f:
                for line in f:
                    line = line.strip()
                    if not line or '=' not in line:
                        continue
                    key, _, val = line.partition('=')
                    key = key.strip()
                    val = val.strip()
                    if key == 'calibrated_offset':
                        self.calibrated_offset = float(val)
                    elif key == 'target_angle' and self._load_target_angle:
                        self.target_angle = float(val)
                    elif key == 'angle_format' and val in ('2d', '1d', '1d_half'):
                        self.angle_format = val
                    elif key == 'board_offset':
                        self.board_offset = float(val)
                    elif key == 'surface_normal':
                        parts = val.split(',')
                        if len(parts) == 3:
                            self.surface_normal = (float(parts[0]), float(parts[1]), float(parts[2]))
                    elif key == 'calibrated_gravity':
                        parts = val.split(',')
                        if len(parts) == 3:
                            self.calibrated_gravity = (float(parts[0]), float(parts[1]), float(parts[2]))
            print("Settings loaded")
        except Exception:
            print("No settings saved, using defaults")

    def save(self):
        try:
            with open('settings.txt', 'w') as f:
                f.write(f"calibrated_offset={self.calibrated_offset}\n")
                f.write(f"target_angle={self.target_angle}\n")
                f.write(f"angle_format={self.angle_format}\n")
                f.write(f"board_offset={self.board_offset}\n")
                if self.surface_normal is not None:
                    nx, ny, nz = self.surface_normal
                    f.write(f"surface_normal={nx:.6f},{ny:.6f},{nz:.6f}\n")
                if self.calibrated_gravity is not None:
                    gx, gy, gz = self.calibrated_gravity
                    f.write(f"calibrated_gravity={gx:.6f},{gy:.6f},{gz:.6f}\n")
        except Exception as e:
            print(f"Settings save error: {e}")

    def reset_calibration(self):
        self.calibrated_offset  = 0.0
        self.target_angle       = 0.0
        self.calibrated_gravity = None
        self.save()
        print("-> CAL/PRESET cleared")

    def reset_board_offset(self):
        self.board_offset   = 0.0
        self.surface_normal = None
        self.save()
        print("-> BOARD OFFSET reset")
