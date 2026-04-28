import ubluetooth
import time
import machine

_IRQ_CENTRAL_CONNECT    = 1
_IRQ_CENTRAL_DISCONNECT = 2
_IRQ_GATTS_WRITE        = 3

_NUS_UUID = ubluetooth.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
_TX_UUID  = ubluetooth.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E')  # device → phone
_RX_UUID  = ubluetooth.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E')  # phone  → device

_ADV_PAYLOAD = (
    b'\x02\x01\x06' +                          # flags: LE general discoverable
    b'\x0c\x09Knife_Level'                      # complete local name (0x0c = 12 = 1 type + 11 chars)
)

_LIVE_INTERVAL_MS = 40

# Settings that live in config.py — changing them requires reboot
_CONFIG_SETTINGS = {
    'show_preset_name':              ('bool',  'SHOW_PRESET_NAME'),
    'show_target_angle':             ('bool',  'SHOW_TARGET_ANGLE'),
    'load_target_angle_from_eeprom': ('bool',  'LOAD_TARGET_ANGLE_FROM_EEPROM'),
    'angle_axis':                    ('str',   'ANGLE_AXIS'),
    'smoothing':                     ('float', 'SMOOTHING'),
    'deviation_threshold':           ('int',   'DEVIATION_THRESHOLD'),
}


class BleUart:
    def __init__(self):
        self._ble         = ubluetooth.BLE()
        self._conn        = None
        self._tx_handle   = None
        self._rx_handle   = None
        self._live         = False
        self._last_send    = 0
        self._cmd_queue    = []   # commands queued from IRQ, processed one per tick()

    def enable(self):
        self._ble.active(True)
        self._ble.irq(self._irq)

        NUS = (
            _NUS_UUID,
            (
                (_TX_UUID, ubluetooth.FLAG_NOTIFY),
                (_RX_UUID, ubluetooth.FLAG_WRITE),
            ),
        )
        ((self._tx_handle, self._rx_handle),) = self._ble.gatts_register_services((NUS,))
        self._ble.gatts_set_buffer(self._rx_handle, 512)
        self._advertise()
        print("BLE UART ready")

    def tick(self, device):
        if self._cmd_queue:
            self._process_command(self._cmd_queue.pop(0), device)

        if self._live and self._conn is not None:
            now = time.ticks_ms()
            if time.ticks_diff(now, self._last_send) >= _LIVE_INTERVAL_MS:
                self._last_send = now
                self.send(f"angle:{device.engine.smooth_angle:.2f}")

    def send(self, text):
        if self._conn is not None:
            try:
                self._ble.gatts_notify(self._conn, self._tx_handle, text.encode())
            except OSError as e:
                if e.errno == 12:  # ENOMEM
                    print(f"BLE send buffer full, waiting... ({repr(text[:30])}...)")
                    time.sleep_ms(50)
                    try:
                        self._ble.gatts_notify(self._conn, self._tx_handle, text.encode())
                    except Exception as e2:
                        print(f"BLE send retry failed: {e2}")
                else:
                    print(f"BLE send error: {e}")

    def send_target_state(self, device):
        self.send(f"target:{device.engine.target_angle:.2f}")
        self.send(f"target_name:{device.engine.target_name or ''}")

    @property
    def connected(self):
        return self._conn is not None

    def _advertise(self):
        self._ble.gap_advertise(100_000, adv_data=_ADV_PAYLOAD)

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            self._conn, _, _ = data
            print("BLE connected")
        elif event == _IRQ_CENTRAL_DISCONNECT:
            self._conn = None
            self._live = False
            self._cmd_queue.clear()
            self._advertise()
            print("BLE disconnected, advertising")
        elif event == _IRQ_GATTS_WRITE:
            raw_bytes = self._ble.gatts_read(self._rx_handle)
            cmd = raw_bytes.decode().strip()
            print(f"BLE RX raw: {repr(raw_bytes)} → decoded: {repr(cmd)}")
            self._cmd_queue.append(cmd)

    def _process_command(self, cmd, device):
        print(f"_process_command: {repr(cmd)}")
        if cmd == "live_start":
            self._live = True
        elif cmd == "live_stop":
            self._live = False
        elif cmd == "get_calibration":
            self._send_calibration(device)
        elif cmd == "get_presets":
            self._send_presets(device)
        elif cmd == "clear_presets":
            self._clear_presets(device)
        elif cmd.startswith("add_preset:"):
            self._add_preset(cmd[11:], device)
        elif cmd.startswith("set_target_angle:"):
            self._set_target_angle(cmd[17:], device)
        elif cmd == "calibrate":
            self._calibrate(device)
        elif cmd == "get_settings":
            self._send_settings(device)
        elif cmd.startswith("set_setting:"):
            self._set_setting(cmd[12:], device)
        elif cmd == "reboot":
            print("Rebooting as requested")
            self.send("ok")
            time.sleep_ms(200)
            machine.reset()

    def _send_settings(self, device):
        from drivers.config_rw import read_config
        for key, (type_, config_key) in _CONFIG_SETTINGS.items():
            val = read_config(config_key)
            if val is not None:
                if type_ == 'bool':
                    val = 'true' if val == 'True' else 'false'
                self.send(f"setting:{key}:{val}")
                time.sleep_ms(20)  # Give BLE stack time to process
        self.send(f"setting:angle_format:{device.settings.angle_format}")
        time.sleep_ms(20)
        self.send("settings_done")

    def _send_calibration(self, device):
        self.send(f"calibration:{device.settings.calibrated_offset:.2f}")

    def _send_presets(self, device):
        for name, angle in device.presets:
            self.send(f"preset:{name}:{abs(angle):.2f}")
            time.sleep_ms(20)
        self.send("presets_done")

    def _clear_presets(self, device):
        try:
            device.presets.replace_all([])
            self.send("ok")
        except Exception:
            self.send("err:preset clear failed")

    def _add_preset(self, args, device):
        name, _, raw_angle = args.partition(':')
        name = name.strip()
        raw_angle = raw_angle.strip()

        if not name or ',' in name or ':' in name:
            self.send("err:invalid preset name")
            return

        try:
            angle = abs(float(raw_angle))
        except Exception:
            self.send("err:invalid preset angle")
            return

        presets = list(device.presets)
        presets.append((name, angle))
        try:
            device.presets.replace_all(presets)
            self.send("ok")
        except Exception:
            self.send("err:preset save failed")

    def _set_target_angle(self, args, device):
        try:
            angle = abs(float(args.strip()))
        except Exception:
            self.send("err:invalid angle")
            return
        name = "Custom"
        for n, a in device.presets:
            if abs(abs(a) - angle) < 1e-6:
                name = n
                break
        device.engine.set_target(angle, name=name)
        device.settings.target_angle = angle
        device.settings.save_calibration()
        print(f"BLE set_target_angle: {angle:.2f}° ({name})")
        self.send_target_state(device)

    def _calibrate(self, device):
        device.engine.calibrate()
        device.settings.calibrated_offset = device.engine.calibrated_offset
        device.settings.save_calibration()
        self._send_calibration(device)
        self.send("ok:calibrated")

    def _set_setting(self, args, device):
        key, _, raw = args.partition(':')
        key = key.strip()
        raw = raw.strip()
        print(f"_set_setting: key={key}, raw={raw}")

        if key == 'angle_format':
            if raw in ('2d', '1d', '1d_half'):
                device.settings.angle_format = raw
                device.engine.angle_format = raw
                device.settings.save_angle_format()
                self.send('ok')
            else:
                self.send('err:invalid format')
            return

        if key not in _CONFIG_SETTINGS:
            self.send('err:unknown key')
            return

        type_, config_key = _CONFIG_SETTINGS[key]
        if type_ == 'bool':
            py_val = 'True' if raw.lower() == 'true' else 'False'
        elif type_ == 'str':
            py_val = f'"{raw}"'
        else:
            py_val = raw
        print(f"_set_setting: type={type_}, config_key={config_key}, py_val={py_val}")

        from drivers.config_rw import write_config
        if write_config(config_key, py_val):
            self.send('ok:reboot_needed')
        else:
            self.send('err:write failed')
