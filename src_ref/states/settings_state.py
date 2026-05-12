from core.state import State
from core.container import Container


class SettingsState(State):
    def __init__(self, items):
        self._items = items
        self._index = 0

    def enter(self):
        self._render()
        Container.logging_service.log("[SettingsState] enter")

    def _render(self):
        lines = []
        for i, item in enumerate(self._items):
            prefix = ">" if i == self._index else " "
            lines.append(prefix + item.label)
        Container.display_service.show_text(*lines)

    def update(self):
        if Container.button_event == 'short_top':
            self._index = (self._index + 1) % len(self._items)
            self._render()
        elif Container.button_event == 'short_low':
            next_state = self._items[self._index].make_state()
            if next_state is not None:
                return next_state
            Container.logging_service.log("[SettingsState] select: " + self._items[self._index].label)
        return None

    def exit(self):
        Container.logging_service.log("[SettingsState] exit")
