from utime import ticks_ms, ticks_diff

_USB_CHECK_INTERVAL_MS = 4000


class App:
    def __init__(self, display, imu, buttons, storage, config,
                 calibration, measure, ble, ble_handler, battery, presets,
                 settings_items, build_angle_items):
        self.display           = display
        self.imu               = imu
        self.buttons           = buttons
        self.storage           = storage
        self.config            = config
        self.calibration       = calibration
        self.measure           = measure
        self.ble               = ble
        self.ble_handler       = ble_handler
        self.battery           = battery
        self.presets           = presets
        self.settings_items    = settings_items
        self.build_angle_items = build_angle_items
        self.button_event      = None
        self._last_usb_check   = 0

    def run(self, initial_state, global_events=None):
        if global_events is None:
            global_events = {}
        state = initial_state
        state.enter(self)
        while True:
            self.button_event = self.buttons.update()
            if self.button_event in global_events:
                state.exit(self)
                state = global_events[self.button_event]()
                state.enter(self)
                continue
            self.ble_handler.tick()
            if ticks_diff(ticks_ms(), self._last_usb_check) >= _USB_CHECK_INTERVAL_MS:
                self._last_usb_check = ticks_ms()
                if self.battery.check_usb():
                    self.button_event = None
            next_state = state.update(self)
            if next_state is not None:
                state.exit(self)
                state = next_state
                state.enter(self)
