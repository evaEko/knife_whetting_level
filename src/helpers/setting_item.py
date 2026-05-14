class SettingItem:
    def __init__(self, label, action=None, handler=None, subtitle=None):
        self.label    = label
        self.subtitle = subtitle
        self._action  = action    # callable(app) -> 'measure'|'settings'|None
        self._handler = handler   # callable() -> SettingHandler

    def select(self, app):
        """Returns 'measure', 'settings', a SettingHandler instance, or None."""
        if self._action:
            return self._action(app)
        if self._handler:
            return self._handler()
        return None
