from core.state import State
from core.container import Container


class AngleSelectState(State):
    _index = 0  # persists across visits

    def __init__(self, items):
        self._items = items
        if AngleSelectState._index >= len(items):
            AngleSelectState._index = 0

    def enter(self):
        self._render()

    def _render(self):
        item = self._items[AngleSelectState._index]
        Container.display_service.show_option(item.label, item.subtitle)

    def update(self):
        if Container.button_event == 'short_top':
            AngleSelectState._index = (AngleSelectState._index + 1) % len(self._items)
            self._render()
        elif Container.button_event == 'short_low':
            next_state = self._items[AngleSelectState._index].make_state()
            if next_state is not None:
                return next_state
        return None

    def exit(self):
        pass
