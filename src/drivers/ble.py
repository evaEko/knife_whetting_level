import ubluetooth
import time

_IRQ_CENTRAL_CONNECT    = 1
_IRQ_CENTRAL_DISCONNECT = 2
_IRQ_GATTS_WRITE        = 3

_NUS_UUID = ubluetooth.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
_TX_UUID  = ubluetooth.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E')
_RX_UUID  = ubluetooth.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E')

_ADV_PAYLOAD = (
    b'\x02\x01\x06' +
    b'\x0c\x09Knife_Level'
)


class BleDriver:
    def __init__(self):
        self._ble       = ubluetooth.BLE()
        self._conn      = None
        self._tx        = None
        self._rx        = None
        self._enabled   = False
        self._cmd_queue = []

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
        ((self._tx, self._rx),) = self._ble.gatts_register_services((NUS,))
        self._ble.gatts_set_buffer(self._rx, 512)
        self._advertise()
        self._enabled = True

    def disable(self):
        try:
            self._ble.gap_advertise(None)
            if self._conn is not None:
                self._ble.gap_disconnect(self._conn)
        except OSError:
            pass
        self._ble.active(False)
        self._conn    = None
        self._enabled = False
        self._cmd_queue.clear()

    def send(self, text):
        if self._conn is None:
            return
        try:
            self._ble.gatts_notify(self._conn, self._tx, text.encode())
        except OSError as e:
            if e.errno == 12:  # ENOMEM — buffer full, retry once
                time.sleep_ms(50)
                try:
                    self._ble.gatts_notify(self._conn, self._tx, text.encode())
                except Exception:
                    pass

    def poll(self):
        """Return next queued command string or None."""
        return self._cmd_queue.pop(0) if self._cmd_queue else None

    def disconnect(self):
        if self._conn is not None:
            try:
                self._ble.gap_disconnect(self._conn)
            except Exception:
                self._conn = None
                self._advertise()

    @property
    def enabled(self):
        return self._enabled

    @property
    def connected(self):
        return self._conn is not None

    def _advertise(self):
        self._ble.gap_advertise(100_000, adv_data=_ADV_PAYLOAD)

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            self._conn, _, _ = data
        elif event == _IRQ_CENTRAL_DISCONNECT:
            self._conn = None
            self._cmd_queue.clear()
            if self._enabled:
                self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            cmd = self._ble.gatts_read(self._rx).decode().strip()
            self._cmd_queue.append(cmd)
