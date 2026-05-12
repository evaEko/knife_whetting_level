import sys
from core.state import State
from core.container import Container


class FlashModeState(State):
    def enter(self):
        Container.display_service.show_text("Flash mode", "connect now")
        Container.logging_service.log("[FlashModeState] enter")
        sys.exit()

    def update(self):
        return None

    def exit(self):
        pass
