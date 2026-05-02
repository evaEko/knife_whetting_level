import time
from config import (
    ANGLE_FORMAT, LOAD_TARGET_ANGLE_FROM_EEPROM,
    SHOW_TARGET_ANGLE, SHOW_PRESET_NAME,
)
from drivers.display import Display
from drivers.sensor import Sensor
from drivers.buttons import Buttons
from domain.angle_engine import AngleEngine
from domain.preset_store import PresetStore
from domain.settings import Settings

# BLE key → (type, config.py variable) for settings the phone can read/write.
_BLE_CONFIG_SETTINGS = {
    'show_preset_name':              ('bool',  'SHOW_PRESET_NAME'),
    'show_target_angle':             ('bool',  'SHOW_TARGET_ANGLE'),
    'load_target_angle_from_eeprom': ('bool',  'LOAD_TARGET_ANGLE_FROM_EEPROM'),
    'smoothing':                     ('float', 'SMOOTHING'),
    'deviation_threshold':           ('int',   'DEVIATION_THRESHOLD'),
}


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

    def reload_config(self):
        """Re-read runtime-mutable config.py values and re-apply all settings."""
        from drivers.config_rw import read_config
        val = read_config('SMOOTHING')
        if val is not None:
            try: self.engine.smoothing = float(val)
            except: pass
        val = read_config('DEVIATION_THRESHOLD')
        if val is not None:
            try: self.engine.deviation_threshold = int(val)
            except: pass
        val = read_config('SHOW_TARGET_ANGLE')
        if val is not None:
            self.show_target_angle = (val != 'False')
        val = read_config('SHOW_PRESET_NAME')
        if val is not None:
            self.show_preset_name = (val != 'False')
        self.settings.load()
        self._sync_engine()

    def handle_command(self, cmd):
        """Dispatch a BLE command string received from the phone."""
        ble = self.ble
        if cmd == 'live_start':
            ble.start_live()
            ble.send_target_state(self)
        elif cmd == 'live_stop':
            ble.stop_live()
        elif cmd == 'get_calibration':
            ble.send(f"calibration:{self.settings.calibrated_offset:.2f}")
        elif cmd == 'get_presets':
            for name, angle in self.presets:
                ble.send(f"preset:{name}:{abs(angle):.2f}")
                time.sleep_ms(20)
            ble.send("presets_done")
        elif cmd == 'clear_presets':
            try:
                self.presets.replace_all([])
                ble.send("ok")
            except Exception:
                ble.send("err:preset clear failed")
        elif cmd.startswith('add_preset:'):
            self._cmd_add_preset(cmd[11:])
        elif cmd.startswith('set_target_angle:'):
            self._cmd_set_target_angle(cmd[17:])
        elif cmd.startswith('set_custom_angle:'):
            self._cmd_set_custom_angle(cmd[17:])
        elif cmd == 'get_target_state':
            ble.send_target_state(self)
        elif cmd == 'app_disconnect':
            ble.disconnect()
        elif cmd == 'calibrate':
            self.engine.calibrate()
            self.settings.calibrated_offset = self.engine.calibrated_offset
            self.settings.save()
            ble.send(f"calibration:{self.settings.calibrated_offset:.2f}")
            ble.send("ok:calibrated")
        elif cmd == 'get_settings':
            self._cmd_get_settings()
        elif cmd.startswith('set_setting:'):
            self._cmd_set_setting(cmd[12:])
        elif cmd == 'reinit':
            print("Reinitialising as requested")
            self.reload_config()
            from states.measure import MeasureState
            if self.state is not None:
                self.state.exit(self)
            self.state = MeasureState()
            self.state.enter(self)
            ble.send("ok")
        elif cmd == 'reboot':
            print("Rebooting as requested")
            ble.send("ok")
            time.sleep_ms(200)
            import machine
            machine.reset()

    def _sync_engine(self):
        """Apply persisted settings into the engine and resolve target name."""
        self.engine.apply(self.settings)
        if self.engine.target_angle != 0.0:
            name = self.presets.find_name(self.engine.target_angle)
            self.engine.target_name = name if name is not None else "Custom"

    # --- BLE command helpers ---

    def _cmd_add_preset(self, args):
        ble = self.ble
        name, _, raw_angle = args.partition(':')
        name      = name.strip()
        raw_angle = raw_angle.strip()
        if not name or ',' in name or ':' in name:
            ble.send("err:invalid preset name")
            return
        try:
            angle = abs(float(raw_angle))
        except Exception:
            ble.send("err:invalid preset angle")
            return
        presets = list(self.presets)
        presets.append((name, angle))
        try:
            self.presets.replace_all(presets)
            ble.send("ok")
        except Exception:
            ble.send("err:preset save failed")

    def _cmd_set_target_angle(self, args):
        ble = self.ble
        try:
            angle = abs(float(args.strip()))
        except Exception:
            ble.send("err:invalid angle")
            return
        name = self.presets.find_name(angle) or "Custom"
        self.engine.set_target(angle, name=name)
        self.settings.target_angle = angle
        self.settings.save()
        print(f"BLE set_target_angle: {angle:.2f}° ({name})")
        ble.send_target_state(self)

    def _cmd_set_custom_angle(self, raw):
        ble = self.ble
        try:
            angle = abs(float(raw.strip()))
        except Exception:
            ble.send("err:invalid angle")
            return
        if angle == 0.0:
            ble.send("err:invalid angle")
            return
        presets = [(n, a) for n, a in self.presets if n != "Custom"]
        presets.append(("Custom", angle))
        try:
            self.presets.replace_all(presets)
        except Exception:
            ble.send("err:preset save failed")
            return
        self.engine.set_target(angle, name="Custom")
        self.settings.target_angle = angle
        self.settings.save()
        print(f"BLE set_custom_angle: {angle:.2f}°")
        ble.send_target_state(self)

    def _cmd_get_settings(self):
        ble = self.ble
        from drivers.config_rw import read_config
        for key, (type_, config_key) in _BLE_CONFIG_SETTINGS.items():
            val = read_config(config_key)
            if val is not None:
                if type_ == 'bool':
                    val = 'true' if val == 'True' else 'false'
                ble.send(f"setting:{key}:{val}")
                time.sleep_ms(20)
        ble.send(f"setting:angle_format:{self.settings.angle_format}")
        time.sleep_ms(20)
        ble.send("settings_done")

    def _cmd_set_setting(self, args):
        ble = self.ble
        key, _, raw = args.partition(':')
        key = key.strip()
        raw = raw.strip()
        print(f"_cmd_set_setting: key={key}, raw={raw}")

        if key == 'angle_format':
            if raw in ('2d', '1d', '1d_half'):
                self.settings.angle_format = raw
                self.engine.angle_format   = raw
                self.settings.save()
                ble.send('ok')
            else:
                ble.send('err:invalid format')
            return

        if key not in _BLE_CONFIG_SETTINGS:
            ble.send('err:unknown key')
            return

        type_, config_key = _BLE_CONFIG_SETTINGS[key]
        if type_ == 'bool':
            py_val = 'True' if raw.lower() == 'true' else 'False'
        elif type_ == 'str':
            py_val = f'"{raw}"'
        else:
            py_val = raw

        from drivers.config_rw import write_config
        if write_config(config_key, py_val):
            ble.send('ok:reboot_needed')
        else:
            ble.send('err:write failed')
