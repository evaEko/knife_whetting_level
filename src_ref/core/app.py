from core.container import Container


class App:
    def run(self, initial_state, global_events=None):
        if global_events is None:
            global_events = {}
        state = initial_state
        state.enter()
        while True:
            Container.button_event = Container.button_service.update()
            if Container.button_event in global_events:
                state.exit()
                state = global_events[Container.button_event]()
                state.enter()
                continue
            next_state = state.update()
            if next_state is not None:
                state.exit()
                state = next_state
                state.enter()
