from config import (
    ANGLE_FORMAT,
    LOAD_TARGET_ANGLE_FROM_EEPROM,
    SHOW_PRESET_NAME,
    SHOW_TARGET_ANGLE,
)
from domain.angle_engine import AngleEngine
from domain.ble_commands import BleCommandHandler
from domain.preset_store import PresetStore
from domain.settings import Settings
from drivers.buttons import Buttons
from drivers.display import Display
from drivers.sensor import Sensor


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
        self.state             = None
        self.ble               = None
        self.show_target_angle = SHOW_TARGET_ANGLE
        self.show_preset_name  = SHOW_PRESET_NAME
        self.ble_handler       = BleCommandHandler(self)

    def run(self):
        from states.boot import BootState
        self.state = BootState()
        self.state.enter(self)
        while True:
            next_state = self.state.update(self)
            if next_state is not None:
                self.state.exit(self)
                self.state = next_state
                self.state.enter(self)

    def transition_to(self, next_state):
        if self.state is not None:
            self.state.exit(self)
        self.state = next_state
        self.state.enter(self)

    def reload_config(self):
        """Re-read runtime-mutable config.py values and re-apply all settings."""
        from drivers.config_rw import read_config
        val = read_config('SMOOTHING')
        if val is not None:
            try: self.engine.smoothing = float(val)
            except: pass
        val = read_config('DEVIATION_THRESHOLD')
        if val is not None:
            try: self.engine.deviation_threshold = float(val)
            except: pass
        val = read_config('SHOW_TARGET_ANGLE')
        if val is not None:
            self.show_target_angle = (val != 'False')
        val = read_config('SHOW_PRESET_NAME')
        if val is not None:
            self.show_preset_name = (val != 'False')
        self.settings.load()
        self._sync_engine()

    def _sync_engine(self):
        """Apply persisted settings into the engine and resolve target name."""
        self.engine.apply(self.settings)
        if self.engine.target_angle != 0.0:
            name = self.presets.find_name(self.engine.target_angle)
            self.engine.target_name = name if name is not None else "Custom"
        if self.settings.surface_normal is not None:
            nx, ny, nz = self.settings.surface_normal
            self.sensor.set_surface_normal(nx, ny, nz)
