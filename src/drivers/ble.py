import ubluetooth
import time

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
        self._live        = False
        self._last_send   = 0
        self._pending_cmd = None  # commands queued from IRQ, processed in tick()

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
        self._advertise()
        print("BLE UART ready")

    def tick(self, device):
        if self._pending_cmd is not None:
            self._process_command(self._pending_cmd, device)
            self._pending_cmd = None

        if self._live and self._conn is not None:
            now = time.ticks_ms()
            if time.ticks_diff(now, self._last_send) >= _LIVE_INTERVAL_MS:
                self._last_send = now
                self.send(f"angle:{device.engine.smooth_angle:.2f}")

    def send(self, text):
        if self._conn is not None:
            self._ble.gatts_notify(self._conn, self._tx_handle, text.encode())

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
            self._pending_cmd = None
            self._advertise()
            print("BLE disconnected, advertising")
        elif event == _IRQ_GATTS_WRITE:
            self._pending_cmd = self._ble.gatts_read(self._rx_handle).decode().strip()

    def _process_command(self, cmd, device):
        if cmd == "live_start":
            self._live = True
        elif cmd == "live_stop":
            self._live = False
        elif cmd == "get_settings":
            self._send_settings(device)
        elif cmd.startswith("set_setting:"):
            self._set_setting(cmd[12:], device)

    def _send_settings(self, device):
        from drivers.config_rw import read_config
        for key, (type_, config_key) in _CONFIG_SETTINGS.items():
            val = read_config(config_key)
            if val is not None:
                if type_ == 'bool':
                    val = 'true' if val == 'True' else 'false'
                self.send(f"setting:{key}:{val}")
        self.send(f"setting:angle_format:{device.settings.angle_format}")
        self.send("settings_done")

    def _set_setting(self, args, device):
        key, _, raw = args.partition(':')
        key = key.strip()
        raw = raw.strip()

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

        from drivers.config_rw import write_config
        if write_config(config_key, py_val):
            self.send('ok:reboot_needed')
        else:
            self.send('err:write failed')
