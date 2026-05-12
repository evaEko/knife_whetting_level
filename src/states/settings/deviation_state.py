from core.state import State

_STEP_FINE   = 0.1
_STEP_COARSE = 0.5
_MIN         = 0.0
_MAX         = 4.0


class DeviationState(State):
    def __init__(self):
        self._value = None

    def enter(self, app):
        self._value = app.config.deviation_threshold
        self._render(app)
        app.logging.log("[DeviationState] enter")

    def update(self, app):
        if app.button_event == 'short_top':
            self._increment(app, _STEP_FINE)
        elif app.button_event == 'long_top':
            self._increment(app, _STEP_COARSE)
        elif app.button_event == 'short_low':
            app.config.set('deviation_threshold', self._value)
            if app.ble.connected:
                app.ble.send("setting:deviation_threshold:{:.1f}".format(self._value))
            app.logging.log("[DeviationState] saved: " + str(self._value))
            from states.settings_state import SettingsState
            return SettingsState(app.settings_items)
        elif app.button_event == 'long_low':
            from states.settings_state import SettingsState
            return SettingsState(app.settings_items)
        return None

    def exit(self, app):
        app.logging.log("[DeviationState] exit")

    def _render(self, app):
        app.display.show_text(
            "Deviation",
            "{:.1f} deg".format(self._value),
            "top:+0.1 long:+0.5",
        )

    def _increment(self, app, step):
        self._value = round(self._value + step, 1)
        if self._value > _MAX:
            self._value = _MIN
        elif self._value < _MIN:
            self._value = _MAX
        self._render(app)
