class SettingItem:
    def __init__(self, label, factory=None, subtitle=None):
        self.label    = label
        self.subtitle = subtitle
        self._factory = factory

    def make_state(self):
        return self._factory() if self._factory else None
