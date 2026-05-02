import time
from state import State
from config import BLE_ENABLED
from drivers.battery import read_battery_pct


class BootState(State):
    def __init__(self):
        self._phase       = 'splash'
        self._wait_until  = None
        self._battery_pct = None

    def enter(self, device):
        device.display.init()
        device.display.show_knife()
        self._wait_until = time.ticks_add(time.ticks_ms(), 1000)

    def update(self, device):
        if self._phase == 'splash':
            if time.ticks_diff(time.ticks_ms(), self._wait_until) < 0:
                return None
            device.buttons.init()
            self._phase = 'battery'
            pct = read_battery_pct()
            device.display.show_battery(pct)
            self._battery_pct = pct
            if pct is not None:
                self._wait_until = time.ticks_add(time.ticks_ms(), 1500)
            return None

        if self._phase == 'battery':
            if self._battery_pct is None:
                pct = read_battery_pct()
                if pct is not None:
                    self._battery_pct = pct
                    device.display.show_battery(pct)
                    self._wait_until = time.ticks_add(time.ticks_ms(), 1500)
                elif device.buttons.is_pressed('low'):
                    self._phase = 'hardware'
                return None
            if time.ticks_diff(time.ticks_ms(), self._wait_until) < 0:
                return None
            self._phase = 'hardware'
            return None

        # 'hardware' phase — init remaining subsystems and hand off
        device.sensor.init()
        device.presets.load()
        if BLE_ENABLED:
            from drivers.ble import BleUart
            device.ble = BleUart()
            device.ble.enable()
        device.settings.load()
        device._sync_engine()
        from states.measure import MeasureState
        return MeasureState()
