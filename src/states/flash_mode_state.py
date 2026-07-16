import sys
from core.state import State
from services.logging import log


class FlashModeState(State):
    def enter(self, app):
        app.display.show_text("Flash mode", "connect now")
        log("[FlashModeState] enter")
        sys.exit()

    def update(self, app):
        return None

    def exit(self, app):
        pass
