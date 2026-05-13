from core.state import State


class AngleSelectState(State):
    _index = 0  # persists across visits

    def __init__(self, items):
        self._items   = items
        self._handler = None
        if AngleSelectState._index >= len(items):
            AngleSelectState._index = 0

    def enter(self, app):
        self._render(app)

    def update(self, app):
        if self._handler:
            result = self._handler.update(app)
            if result is not None:
                self._handler.exit(app)
                self._handler = None
                from states.measure_state import MeasureState
                return MeasureState()
            return None

        if app.button_event == 'short_top':
            AngleSelectState._index = (AngleSelectState._index + 1) % len(self._items)
            self._render(app)
        elif app.button_event == 'short_low':
            result = self._items[AngleSelectState._index].select(app)
            if result == 'measure':
                from states.measure_state import MeasureState
                return MeasureState()
            if result not in (None, 'settings'):
                self._handler = result
                self._handler.enter(app)
        return None

    def exit(self, app):
        pass

    def _render(self, app):
        item = self._items[AngleSelectState._index]
        app.display.show_option(item.label, item.subtitle)
