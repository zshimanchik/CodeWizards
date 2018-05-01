from debug_client import DebugClient
from model.Game import Game
from model.Move import Move
from model.Wizard import Wizard
from model.World import World

from constants import *


class Drawer:
    def __init__(self):
        self.debug = DebugClient()

    def draw_all(self, strategy, me: Wizard, world: World, game: Game, move: Move):
        self.strategy = strategy
        self.me = me
        self.world = world
        self.game = game
        self.move = move

        with self.debug.pre() as drawer:
            self.draw_matrix(drawer)
            self.draw_map(drawer)

        with self.debug.abs() as drawer:
            self.draw_text(drawer)

    def draw_matrix(self, drawer):
        matrix_top = self.me.y - MATRIX_CELL_SIZE * MATRIX_CELL_AMOUNT / 2
        matrix_left = self.me.x - MATRIX_CELL_SIZE * MATRIX_CELL_AMOUNT / 2
        for row, row_value in enumerate(self.strategy.matrix):
            for col, value in enumerate(row_value):
                if value == 0:
                    color = (0.9, 0.9, 0.9)
                elif value == 666:
                    color = (0.9, 0.6, 0.6)
                elif value > 0:
                    color_value = min(0.9, value / 30)
                    color = (0.9 - color_value, 0.9, 0.9 - color_value)
                else:
                    color = (0.8, 0.8, 1)
                drawer.fill_rect(
                    matrix_left + col * MATRIX_CELL_SIZE + 1,
                    matrix_top + row * MATRIX_CELL_SIZE + 1,
                    matrix_left + (col + 1) * MATRIX_CELL_SIZE - 1,
                    matrix_top + (row + 1) * MATRIX_CELL_SIZE - 1,
                    color
                )

    def draw_text(self, drawer):
        keyboard_wizard = [w for w in self.world.wizards if w.id == 2][0]
        text = [
            f'tick: {self.world.tick_index}',
            f'{int(self.me.x)}, {int(self.me.y)}',
            str(self.strategy.move_state),
            str(self.strategy.line_state),
            f'{int(keyboard_wizard.x)}, {int(keyboard_wizard.y)}'
        ]

        for i, line in enumerate(text):
            drawer.text(600, 300 + i * 14, line, (1, 0, 0))

    def draw_map(self, drawer):
        for map_point in self.strategy.map:
            drawer.fill_circle(map_point.x, map_point.y, 10, (0, 0, 1))
            for neighbor in map_point.neighbors:
                drawer.line(map_point.x, map_point.y, neighbor.x, neighbor.y, (0, 0, 1))
