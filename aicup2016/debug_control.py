class DebugControl:
    def __init__(self, strategy, input_event):
        self.strategy = strategy
        input_event.subscribe(self.handle_input)

    def handle_input(self, input):
        if input == 'f':
            self.strategy.drawer.draw_potential_map = not self.strategy.drawer.draw_potential_map
