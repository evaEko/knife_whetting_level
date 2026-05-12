from core.state import State

class IdleState(State):
    def enter(self, app):
        app.display_service.show_text("Ready")
        app.logging_service.log("[IdleState] enter")
