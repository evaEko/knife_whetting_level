from utime import ticks_ms, ticks_diff
from drivers.ble import BleDriver

_LIVE_INTERVAL_MS = 40


class BleService:
    def __init__(self):
        self._driver    = BleDriver()
        self._live      = False
        self._last_send = 0

    def toggle(self):
        if self._driver.enabled:
            self._driver.disable()
        else:
            self._driver.enable()

    def send(self, text):
        self._driver.send(text)

    def poll(self):
        return self._driver.poll()

    def disconnect(self):
        self._live = False
        self._driver.disconnect()

    def start_live(self):
        self._live = True

    def stop_live(self):
        self._live = False

    def update(self, pitch):
        if not self._live or not self._driver.connected:
            return
        now = ticks_ms()
        if ticks_diff(now, self._last_send) >= _LIVE_INTERVAL_MS:
            self._last_send = now
            self.send("angle:{:.2f}".format(pitch))

    def send_target_state(self, target_angle, name=''):
        angle = target_angle if target_angle is not None else 0.0
        self.send("target_state:{:.2f}:{}".format(angle, name))

    @property
    def enabled(self):
        return self._driver.enabled

    @property
    def connected(self):
        return self._driver.connected
