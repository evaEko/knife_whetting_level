import time
import machine


class BleCommandHandler:
    def __init__(self, ble_service, calibration_service, measure_service,
                 preset_store, config_service, imu_service):
        self._ble         = ble_service
        self._calibration = calibration_service
        self._measure     = measure_service
        self._presets     = preset_store
        self._config      = config_service
        self._imu         = imu_service

    def tick(self):
        """Call once per loop tick from MeasureState."""
        cmd = self._ble.poll()
        if cmd:
            self.handle(cmd)
        if self._calibration.has_stone():
            self._ble.update(
                pitch=self._measure.pitch(),
                target_angle=self._calibration.target_angle(),
            )

    def handle(self, cmd):
        if cmd == 'live_start':
            self._ble.start_live()
            self._send_target_state()
        elif cmd == 'live_stop':
            self._ble.stop_live()
        elif cmd == 'get_calibration':
            self._ble.send("calibration:0.00")
        elif cmd == 'get_presets':
            for name, angle in self._presets:
                self._ble.send("preset:{}:{:.2f}".format(name, abs(angle)))
                time.sleep_ms(20)
            self._ble.send("presets_done")
        elif cmd == 'clear_presets':
            self._presets.replace_all([])
            self._ble.send("ok")
        elif cmd.startswith('add_preset:'):
            self._cmd_add_preset(cmd[11:])
        elif cmd.startswith('set_target_angle:'):
            self._cmd_set_target_angle(cmd[17:])
        elif cmd.startswith('set_custom_angle:'):
            self._cmd_set_custom_angle(cmd[17:])
        elif cmd == 'get_target_state':
            self._send_target_state()
        elif cmd == 'app_disconnect':
            self._ble.disconnect()
        elif cmd == 'calibrate':
            self._cmd_calibrate()
        elif cmd == 'get_settings':
            self._cmd_get_settings()
        elif cmd.startswith('set_setting:'):
            self._cmd_set_setting(cmd[12:])
        elif cmd == 'reinit':
            self._calibration.load()
            self._ble.send("ok")
        elif cmd == 'reboot':
            self._ble.send("ok")
            time.sleep_ms(200)
            machine.reset()

    # ------------------------------------------------------------------ helpers

    def _send_target_state(self):
        angle = self._calibration.target_angle()
        name  = self._find_preset_name(angle) or ''
        self._ble.send_target_state(angle, name)

    def _find_preset_name(self, angle):
        if angle is None:
            return None
        for name, a in self._presets:
            if abs(a - angle) < 0.01:
                return name
        return None

    # ---------------------------------------------------------------- commands

    def _cmd_add_preset(self, args):
        name, _, raw = args.partition(':')
        name = name.strip()
        if not name or ',' in name or ':' in name:
            self._ble.send("err:invalid preset name")
            return
        try:
            angle = abs(float(raw.strip()))
        except Exception:
            self._ble.send("err:invalid preset angle")
            return
        presets = list(self._presets)
        presets.append((name, angle))
        self._presets.replace_all(presets)
        self._ble.send("ok")

    def _cmd_set_target_angle(self, args):
        try:
            angle = abs(float(args.strip()))
        except Exception:
            self._ble.send("err:invalid angle")
            return
        self._calibration.set_target_angle(angle)
        self._send_target_state()

    def _cmd_set_custom_angle(self, raw):
        try:
            angle = abs(float(raw.strip()))
        except Exception:
            self._ble.send("err:invalid angle")
            return
        if angle == 0.0:
            self._ble.send("err:invalid angle")
            return
        presets = [(n, a) for n, a in self._presets if n != "Custom"]
        presets.append(("Custom", angle))
        self._presets.replace_all(presets)
        self._calibration.set_target_angle(angle)
        self._send_target_state()

    def _cmd_calibrate(self):
        self._imu.update()  # drain any pending packets; use last known quaternion if none
        g = self._imu.get_gravity()
        fmt = "{:.6f},{:.6f},{:.6f}".format(g[0], g[1], g[2])
        from helpers.vector_parser import VectorParser
        self._calibration._n_stone = VectorParser.parse(fmt)
        self._calibration._storage.set('n_stone', fmt)
        self._measure.reset_pitch()  # clear smoothing so display snaps to 0° immediately
        self._ble.send("calibration:0.00")
        self._ble.send("ok:calibrated")

    _SETTING_KEYS = [
        'deviation_threshold',
        'capture_delay_sec',
    ]

    def _cmd_get_settings(self):
        for key in self._SETTING_KEYS:
            val = getattr(self._config, key, None)
            if val is None:
                continue
            if key == 'deviation_threshold':
                self._ble.send("setting:{}:{:.1f}".format(key, val))
            elif key == 'capture_delay_sec':
                self._ble.send("setting:{}:{}".format(key, int(val)))
            else:
                self._ble.send("setting:{}:{}".format(key, val))
            time.sleep_ms(20)
        self._ble.send("settings_done")

    def _cmd_set_setting(self, args):
        key, _, raw = args.partition(':')
        key = key.strip()
        raw = raw.strip()
        if key not in self._SETTING_KEYS:
            self._ble.send("err:unknown key")
            return
        if key == 'deviation_threshold':
            try:
                val = float(raw)
            except Exception:
                self._ble.send("err:invalid value")
                return
            self._config.set('deviation_threshold', val)
        elif key == 'capture_delay_sec':
            try:
                val = int(raw)
                if val < 1 or val > 30:
                    raise ValueError()
            except Exception:
                self._ble.send("err:invalid value")
                return
            self._config.set('capture_delay_sec', val)
        else:
            self._config.set(key, raw)
        self._ble.send("ok")
