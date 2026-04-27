class Settings:
    def __init__(self, default_angle_format="1d_half", load_target_angle=True):
        self.calibrated_offset = 0.0
        self.target_angle      = 0.0
        self.angle_format      = default_angle_format
        self.board_offset      = 0.0
        self._load_target_angle = load_target_angle

    def load(self):
        self._load_calibration()
        self._load_angle_format()
        self._load_board_offset()

    # --- calibration / target angle ---

    def _load_calibration(self):
        try:
            with open('settings.txt') as f:
                lines = [ln.strip() for ln in f if ln.strip()]
            if lines:
                self.calibrated_offset = float(lines[0])
            if self._load_target_angle and len(lines) >= 2:
                self.target_angle = float(lines[1])
            print("Settings loaded")
        except Exception:
            print("No settings saved, using defaults")

    def save_calibration(self):
        try:
            with open('settings.txt', 'w') as f:
                f.write(f"{self.calibrated_offset}\n{self.target_angle}\n")
        except Exception as e:
            print(f"Settings save error: {e}")

    def reset_calibration(self):
        self.calibrated_offset = 0.0
        self.target_angle      = 0.0
        self.save_calibration()
        print("-> CAL/PRESET cleared")

    # --- angle format ---

    def _load_angle_format(self):
        try:
            with open('angle_format.txt') as f:
                fmt = f.read().strip()
            if fmt in ("2d", "1d", "1d_half"):
                self.angle_format = fmt
                print(f"Angle format loaded: {fmt}")
        except Exception:
            print(f"No angle format saved, using default: {self.angle_format}")

    def save_angle_format(self):
        try:
            with open('angle_format.txt', 'w') as f:
                f.write(self.angle_format)
            print(f"-> ANGLE FORMAT saved: {self.angle_format}")
        except Exception as e:
            print(f"Angle format save error: {e}")

    # --- board offset ---

    def _load_board_offset(self):
        try:
            with open('board_offset.txt') as f:
                self.board_offset = float(f.read().strip())
            print(f"Board level loaded: {self.board_offset:+.2f}")
        except Exception:
            print("No board level saved, using 0.0")

    def save_board_offset(self, value=None):
        if value is not None:
            self.board_offset = value
        try:
            with open('board_offset.txt', 'w') as f:
                f.write(str(self.board_offset))
            print(f"-> BOARD OFFSET saved: {self.board_offset:+.2f}")
        except Exception as e:
            print(f"Save error: {e}")

    def reset_board_offset(self):
        self.save_board_offset(0.0)
