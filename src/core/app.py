class App:
    def __init__(self, display, logging, imu, buttons, storage, config,
                 calibration, measure, ble, ble_handler, battery, presets,
                 settings_items, build_angle_items):
        self.display           = display
        self.logging           = logging
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
            next_state = state.update(self)
            if next_state is not None:
                state.exit(self)
                state = next_state
                state.enter(self)
