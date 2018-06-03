from threading import Thread


class DebugControl:
    def __init__(self, strategy):
        self.strategy = strategy

    def start(self):

        Thread(target=self.worker, daemon=False).start()

    def worker(self):
        while True:
            self.handle_input(input())

    def handle_input(self, input):
        if input == 'f':
            self.strategy.drawer.draw_potential_map = not self.strategy.drawer.draw_potential_map


