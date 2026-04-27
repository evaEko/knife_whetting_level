import ubluetooth

_IRQ_CENTRAL_CONNECT    = 1
_IRQ_CENTRAL_DISCONNECT = 2
_IRQ_GATTS_WRITE        = 3

_NUS_UUID = ubluetooth.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
_TX_UUID  = ubluetooth.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E')  # device → phone
_RX_UUID  = ubluetooth.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E')  # phone  → device

_ADV_PAYLOAD = (
    b'\x02\x01\x06' +                          # flags: LE general discoverable
    b'\x0b\x09KnifeLevel'                       # complete local name (0x0b = 11 = 1 type + 10 chars)
)


class BleUart:
    def __init__(self):
        self._ble        = ubluetooth.BLE()
        self._conn       = None
        self._tx_handle  = None
        self._rx_handle  = None

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
            self._advertise()
            print("BLE disconnected, advertising")
        elif event == _IRQ_GATTS_WRITE:
            self.send('Hello World')
