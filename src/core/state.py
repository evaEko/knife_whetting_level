class State:
    def enter(self, app):
        pass

    def update(self, app):
        return None  # return next State to transition, None to stay

    def exit(self, app):
        pass
