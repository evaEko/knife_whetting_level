from drivers.ble import BleDriver


class BleService:
    def __init__(self):
        self._driver = BleDriver()

    def toggle(self):
        if self._driver.enabled:
            self._driver.disable()
        else:
            self._driver.enable()

    @property
    def enabled(self):
        return self._driver.enabled

    @property
    def connected(self):
        return self._driver.connected
