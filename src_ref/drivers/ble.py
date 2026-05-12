import ubluetooth

_IRQ_CENTRAL_CONNECT    = 1
_IRQ_CENTRAL_DISCONNECT = 2

_NUS_UUID = ubluetooth.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
_TX_UUID  = ubluetooth.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E')
_RX_UUID  = ubluetooth.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E')

_ADV_PAYLOAD = (
    b'\x02\x01\x06' +
    b'\x0c\x09Knife_Level'
)


class BleDriver:
    def __init__(self):
        self._ble     = ubluetooth.BLE()
        self._conn    = None
        self._enabled = False

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
        self._ble.gatts_register_services((NUS,))
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
            if self._enabled:
                self._advertise()
