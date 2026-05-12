import time

import machine

# BLE key → (type, config.py variable) for settings the phone can read/write.
_BLE_CONFIG_SETTINGS = {
    'show_preset_name':              ('bool',  'SHOW_PRESET_NAME'),
    'show_target_angle':             ('bool',  'SHOW_TARGET_ANGLE'),
    'load_target_angle_from_eeprom': ('bool',  'LOAD_TARGET_ANGLE_FROM_EEPROM'),
    'smoothing':                     ('float', 'SMOOTHING'),
    'deviation_threshold':           ('float', 'DEVIATION_THRESHOLD'),
}


class BleCommandHandler:
    def __init__(self, device):
        self._device = device

    def handle(self, cmd):
        device = self._device
        ble    = device.ble
        if cmd == 'live_start':
            ble.start_live()
            ble.send_target_state(device)
        elif cmd == 'live_stop':
            ble.stop_live()
        elif cmd == 'get_calibration':
            ble.send(f"calibration:{device.settings.calibrated_offset:.2f}")
        elif cmd == 'get_presets':
            for name, angle in device.presets:
                ble.send(f"preset:{name}:{abs(angle):.2f}")
                time.sleep_ms(20)
            ble.send("presets_done")
        elif cmd == 'clear_presets':
            try:
                device.presets.replace_all([])
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
            ble.send_target_state(device)
        elif cmd == 'app_disconnect':
            ble.disconnect()
        elif cmd == 'calibrate':
            device.engine.calibrate()
            device.settings.calibrated_offset = device.engine.calibrated_offset
            g = device.sensor.get_gravity()
            if g is not None:
                device.settings.calibrated_gravity = g
                device.sensor.set_calibrated_g(*g)
            device.settings.save()
            ble.send(f"calibration:{device.settings.calibrated_offset:.2f}")
            ble.send("ok:calibrated")
        elif cmd == 'get_settings':
            self._cmd_get_settings()
        elif cmd.startswith('set_setting:'):
            self._cmd_set_setting(cmd[12:])
        elif cmd == 'reinit':
            print("Reinitialising as requested")
            device.reload_config()
            from states.measure import MeasureState
            device.transition_to(MeasureState())
            ble.send("ok")
        elif cmd == 'reboot':
            print("Rebooting as requested")
            ble.send("ok")
            time.sleep_ms(200)
            machine.reset()

    def _cmd_add_preset(self, args):
        device = self._device
        ble    = device.ble
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
        presets = list(device.presets)
        presets.append((name, angle))
        try:
            device.presets.replace_all(presets)
            ble.send("ok")
        except Exception:
            ble.send("err:preset save failed")

    def _cmd_set_target_angle(self, args):
        device = self._device
        ble    = device.ble
        try:
            angle = abs(float(args.strip()))
        except Exception:
            ble.send("err:invalid angle")
            return
        name = device.presets.find_name(angle) or "Custom"
        device.engine.set_target(angle, name=name)
        device.settings.target_angle = angle
        device.settings.save()
        print(f"BLE set_target_angle: {angle:.2f}° ({name})")
        ble.send_target_state(device)

    def _cmd_set_custom_angle(self, raw):
        device = self._device
        ble    = device.ble
        try:
            angle = abs(float(raw.strip()))
        except Exception:
            ble.send("err:invalid angle")
            return
        if angle == 0.0:
            ble.send("err:invalid angle")
            return
        presets = [(n, a) for n, a in device.presets if n != "Custom"]
        presets.append(("Custom", angle))
        try:
            device.presets.replace_all(presets)
        except Exception:
            ble.send("err:preset save failed")
            return
        device.engine.set_target(angle, name="Custom")
        device.settings.target_angle = angle
        device.settings.save()
        print(f"BLE set_custom_angle: {angle:.2f}°")
        ble.send_target_state(device)

    def _cmd_get_settings(self):
        device = self._device
        ble    = device.ble
        from drivers.config_rw import read_config
        for key, (type_, config_key) in _BLE_CONFIG_SETTINGS.items():
            val = read_config(config_key)
            if val is not None:
                if type_ == 'bool':
                    val = 'true' if val == 'True' else 'false'
                ble.send(f"setting:{key}:{val}")
                time.sleep_ms(20)
        ble.send(f"setting:angle_format:{device.settings.angle_format}")
        time.sleep_ms(20)
        ble.send("settings_done")

    def _cmd_set_setting(self, args):
        device = self._device
        ble    = device.ble
        key, _, raw = args.partition(':')
        key = key.strip()
        raw = raw.strip()
        print(f"_cmd_set_setting: key={key}, raw={raw}")

        if key == 'angle_format':
            if raw in ('2d', '1d', '1d_half'):
                device.settings.angle_format = raw
                device.engine.angle_format   = raw
                device.settings.save()
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
