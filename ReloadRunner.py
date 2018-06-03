import sys
from threading import Thread

from RemoteProcessClient import RemoteProcessClient
from debug_client import DebugClient
from model.Move import Move


class Runner:
    def __init__(self):
        self.reload = True
        self.debug_client = DebugClient()
        self.input_event = EventEmitter()
        self.strategies = []
        if sys.argv.__len__() == 4:
            self.remote_process_client = RemoteProcessClient(sys.argv[1], int(sys.argv[2]))
            self.token = sys.argv[3]
        else:
            self.remote_process_client = RemoteProcessClient("127.0.0.1", 31001)
            self.token = "0000000000000000"

    def run(self):
        try:
            self.remote_process_client.write_token_message(self.token)
            self.remote_process_client.write_protocol_version_message()
            team_size = self.remote_process_client.read_team_size_message()
            game = self.remote_process_client.read_game_context_message()

            self.strategies = []
            self.start_input()
            world_time = 0

            while True:
                if self.reload:
                    print(f'actually reloading at {world_time}')
                    my_modules = ['constants', 'debug_client', 'debug_control', 'drawer', 'MyStrategy', 'potential_map', 'utils']
                    for module in my_modules:
                        if module in sys.modules:
                            del sys.modules[module]
                    import MyStrategy

                    self.strategies = []
                    for _ in range(team_size):
                        self.strategies.append(
                            MyStrategy.MyStrategy(
                                debug_client=self.debug_client,
                                input_event=self.input_event
                            )
                        )
                    self.reload = False

                player_context = self.remote_process_client.read_player_context_message()
                if player_context is None:
                    break
                world_time = player_context.world.tick_index

                player_wizards = player_context.wizards
                if player_wizards is None or player_wizards.__len__() != team_size:
                    break

                moves = []

                for wizard_index in range(team_size):
                    player_wizard = player_wizards[wizard_index]

                    move = Move()
                    moves.append(move)
                    self.strategies[wizard_index].move(player_wizard, player_context.world, game, move)

                self.remote_process_client.write_moves_message(moves)
        finally:
            self.remote_process_client.close()

    def start_input(self):
        Thread(target=self.worker, daemon=False).start()

    def worker(self):
        while True:
            self.handle_input(input())

    def handle_input(self, input):
        if input == 'r':
            self.reload = True
            print('reloading')
        else:
            self.input_event.emit(input)
            # self.strategies[0].debug_control.handle_input(input)


class EventEmitter:
    def __init__(self):
        self.subscriber = None

    def subscribe(self, callback):
        self.subscriber = callback

    def emit(self, data):
        if self.subscriber is not None:
            self.subscriber(data)


import time
time.sleep(2)
Runner().run()
