from core.state import State
from core.container import Container

_STEP = 0.5
_MIN  = 0.5
_MAX  = 10.0


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
            str(self._value) + " deg",
            "low:save",
        )

    def update(self):
        if Container.button_event == 'short_top':
            self._value = min(_MAX, round(self._value + _STEP, 0.5))
            self._render()
        elif Container.button_event == 'short_low':
            Container.config_service.set('deviation_threshold', self._value)
            Container.logging_service.log("[DeviationState] saved: " + str(self._value))
            from states.settings_state import SettingsState
            return SettingsState(Container.settings_items)
        elif Container.button_event == 'long_low':
            from states.settings_state import SettingsState
            return SettingsState(Container.settings_items)
        return None

    def exit(self):
        Container.logging_service.log("[DeviationState] exit")
