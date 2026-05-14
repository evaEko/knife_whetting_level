from core.state import State


class SettingsState(State):
    def __init__(self, items, active_handler=None):
        self._items   = items
        self._index   = 0
        self._handler = active_handler

    def enter(self, app):
        app.logging.log("[SettingsState] enter")
        if self._handler:
            self._handler.enter(app)
        else:
            self._render(app)

    def update(self, app):
        if self._handler:
            return self._handle_active(app)
        return self._handle_menu(app)

    def exit(self, app):
        app.logging.log("[SettingsState] exit")

    def _handle_active(self, app):
        result = self._handler.update(app)
        if result == 'measure':
            self._handler.exit(app)
            self._handler = None
            from states.measure_state import MeasureState
            return MeasureState()
        if result == 'settings':
            self._handler.exit(app)
            self._handler = None
            self._render(app)
        return None

    def _handle_menu(self, app):
        if app.button_event == 'short_top':
            self._index = (self._index + 1) % len(self._items)
            self._render(app)
        elif app.button_event == 'short_low':
            result = self._items[self._index].select(app)
            if result == 'measure':
                from states.measure_state import MeasureState
                return MeasureState()
            if result not in (None, 'settings'):
                self._handler = result
                self._handler.enter(app)
        return None

    def _render(self, app):
        lines = []
        for i, item in enumerate(self._items):
            prefix = ">" if i == self._index else " "
            lines.append(prefix + item.label)
        app.display.show_text(*lines)
