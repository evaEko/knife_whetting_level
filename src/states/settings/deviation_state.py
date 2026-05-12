from core.state import State
from core.container import Container

_STEP_FINE   = 0.1
_STEP_COARSE = 0.5
_MIN         = 0.0
_MAX         = 4.0


class DeviationState(State):
    def __init__(self):
        self._value = None

    def enter(self):
        self._value = Container.config_service.deviation_threshold
        self._render()
        Container.logging_service.log("[DeviationState] enter")

    def _render(self):
        Container.display_service.show_text(
            "Deviation",
            "{:.1f} deg".format(self._value),
            "top:+0.1 long:+0.5",
        )

    def _increment(self, step):
        self._value = round(self._value + step, 1)
        if self._value > _MAX:
            self._value = _MIN
        elif self._value < _MIN:
            self._value = _MAX
        self._render()

    def update(self):
        if Container.button_event == 'short_top':
            self._increment(_STEP_FINE)
        elif Container.button_event == 'long_top':
            self._increment(_STEP_COARSE)
        elif Container.button_event == 'short_low':
            Container.config_service.set('deviation_threshold', self._value)
            if Container.ble_service.connected:
                Container.ble_service.send("setting:deviation_threshold:{:.1f}".format(self._value))
            Container.logging_service.log("[DeviationState] saved: " + str(self._value))
            from states.settings_state import SettingsState
            return SettingsState(Container.settings_items)
        elif Container.button_event == 'long_low':
            from states.settings_state import SettingsState
            return SettingsState(Container.settings_items)
        return None

    def exit(self):
        Container.logging_service.log("[DeviationState] exit")
