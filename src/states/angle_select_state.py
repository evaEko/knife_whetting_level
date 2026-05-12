from core.state import State


class AngleSelectState(State):
    _index = 0  # persists across visits

    def __init__(self, items):
        self._items = items
        if AngleSelectState._index >= len(items):
            AngleSelectState._index = 0

    def enter(self, app):
        self._render(app)

    def update(self, app):
        if app.button_event == 'short_top':
            AngleSelectState._index = (AngleSelectState._index + 1) % len(self._items)
            self._render(app)
        elif app.button_event == 'short_low':
            next_state = self._items[AngleSelectState._index].make_state()
            if next_state is not None:
                return next_state
        return None

    def exit(self, app):
        pass

    def _render(self, app):
        item = self._items[AngleSelectState._index]
        app.display.show_option(item.label, item.subtitle)
