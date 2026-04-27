class State:
    def enter(self, device):
        """Called once when this state becomes active."""
        return None

    def update(self, device):
        """Process one tick. Return next State to transition, or None to stay."""
        return None

    def exit(self, device):
        """Called once before transitioning away from this state."""
        return None
