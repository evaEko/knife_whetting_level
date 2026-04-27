import time
from config import ANGLE_FORMAT, LOAD_TARGET_ANGLE_FROM_EEPROM
from drivers.display import Display
from drivers.sensor import Sensor
from drivers.buttons import Buttons
from drivers.battery import read_battery_pct
from domain.angle_engine import AngleEngine
from domain.preset_store import PresetStore
from domain.settings import Settings


class Device:
    def __init__(self):
        self.display  = Display()
        self.sensor   = Sensor()
        self.buttons  = Buttons()
        self.engine   = AngleEngine()
        self.presets  = PresetStore()
        self.settings = Settings(
            default_angle_format=ANGLE_FORMAT,
            load_target_angle=LOAD_TARGET_ANGLE_FROM_EEPROM,
        )
        self.state = None

    def init(self):
        self.display.init()
        self.display.show_knife()

        self.buttons.init()
        self._check_battery()

        self.sensor.init()
        self.presets.load()

        self.settings.load()
        self._apply_settings()

        from states.measure import MeasureState
        self.state = MeasureState()

    def run(self):
        self.init()
        while True:
            next_state = self.state.update(self)
            if next_state is not None:
                self.state = next_state

    # --- private ---

    def _apply_settings(self):
        """Copy persisted values into the engine after settings are loaded."""
        s = self.settings
        self.engine.board_offset      = s.board_offset
        self.engine.calibrated_offset = s.calibrated_offset
        self.engine.target_angle      = s.target_angle
        self.engine.angle_format      = s.angle_format

    def _check_battery(self):
        pct = read_battery_pct()
        self.display.show_battery(pct)
        if pct is None:
            while True:
                time.sleep_ms(50)
                if self.buttons.is_pressed('low'):
                    break
                pct = read_battery_pct()
                if pct is not None:
                    self.display.show_battery(pct)
                    break
        if pct is not None:
            time.sleep_ms(1500)
