import sys
from state import State


class FlashState(State):
    def update(self, device):
        device.display.invert(False)
        device.display.show_message("Ready to", "flash...")
        print("-> REPL")
        sys.exit()
