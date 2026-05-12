from core.state import State


class SettingsState(State):
    def __init__(self, items):
        self._items = items
        self._index = 0

    def enter(self, app):
        self._render(app)
        app.logging.log("[SettingsState] enter")

    def update(self, app):
        if app.button_event == 'short_top':
            self._index = (self._index + 1) % len(self._items)
            self._render(app)
        elif app.button_event == 'short_low':
            next_state = self._items[self._index].make_state()
            if next_state is not None:
                return next_state
            app.logging.log("[SettingsState] select: " + self._items[self._index].label)
        return None

    def exit(self, app):
        app.logging.log("[SettingsState] exit")

    def _render(self, app):
        lines = []
        for i, item in enumerate(self._items):
            prefix = ">" if i == self._index else " "
            lines.append(prefix + item.label)
        app.display.show_text(*lines)
