import ubluetooth
import time

_IRQ_CENTRAL_CONNECT    = 1
_IRQ_CENTRAL_DISCONNECT = 2
_IRQ_GATTS_WRITE        = 3

_NUS_UUID = ubluetooth.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
_TX_UUID  = ubluetooth.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E')  # device → phone
_RX_UUID  = ubluetooth.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E')  # phone  → device

_ADV_PAYLOAD = (
    b'\x02\x01\x06' +           # flags: LE general discoverable
    b'\x0c\x09Knife_Level'      # complete local name
)

_LIVE_INTERVAL_MS         = 40
_TARGET_STATE_INTERVAL_MS = 1_000


class BleUart:
    def __init__(self):
        self._ble              = ubluetooth.BLE()
        self._conn             = None
        self._tx_handle        = None
        self._rx_handle        = None
        self._live             = False
        self._last_send        = 0
        self._last_target_send = 0
        self._cmd_queue        = []

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
            device.handle_command(self._cmd_queue.pop(0))

        if self._live and self._conn is not None:
            now = time.ticks_ms()
            if time.ticks_diff(now, self._last_send) >= _LIVE_INTERVAL_MS:
                self._last_send = now
                self.send(f"angle:{device.engine.smooth_angle:.2f}")
            if time.ticks_diff(now, self._last_target_send) >= _TARGET_STATE_INTERVAL_MS:
                self._last_target_send = now
                self.send_target_state(device)

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
        name = device.engine.target_name or ''
        self.send(f"target_state:{device.engine.target_angle:.2f}:{name}")

    def start_live(self):
        self._live = True
        self._last_target_send = 0

    def stop_live(self):
        self._live = False

    def disconnect(self):
        self._live = False
        if self._conn is not None:
            try:
                self._ble.gap_disconnect(self._conn)
            except Exception as e:
                print(f"BLE app_disconnect failed: {e}")
                self._conn = None
                self._advertise()

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
