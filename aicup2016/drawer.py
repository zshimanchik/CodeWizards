from aicup2016.constants import *
from aicup2016.potential_map import PotentialMap
from aicup2016.utils import distance2
from model.Game import Game
from model.Move import Move
from model.Wizard import Wizard
from model.World import World


class Drawer:
    def __init__(self, debug_client):
        self.debug = debug_client
        self.draw_potential_map = False

    def draw_all(self, strategy, me: Wizard, world: World, game: Game, move: Move):
        self.strategy = strategy
        self.me = me
        self.world = world
        self.game = game
        self.move = move

        with self.debug.pre() as drawer:
            if self.draw_potential_map:
                self._draw_potential_map(drawer)
            # self.draw_matrix(drawer)
        #     self.draw_map(drawer)

        with self.debug.abs() as drawer:
            self.draw_text(drawer)

    def _draw_potential_map(self, drawer):
        pm = self.strategy.potential_map
        assert isinstance(pm, PotentialMap)
        max_value = pm.map.max()
        for row in range(pm.CELL_AMOUNT):
            for col in range(pm.CELL_AMOUNT):
                x = col * pm.CELL_SIZE + pm.HALF_CELL_SIZE
                y = row * pm.CELL_SIZE + pm.HALF_CELL_SIZE

                if distance2(self.me.x, self.me.y, x, y) < 1000000:
                    if pm.map[row, col] > 0:
                        color_value = min(0.9, pm.map[row, col] / max_value)
                        color = (0.9 - color_value, 0.9, 0.9 - color_value)
                        drawer.fill_circle(x, y, 5, color)
                    else:
                        color_value = min(0.9, -pm.map[row, col] / max_value)
                        color = (0.9, 0.9 - color_value, 0.9 - color_value)
                        drawer.fill_circle(x, y, 5, color)



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
        keyboard_wizard = [w for w in self.world.wizards if w.id == 2]
        if keyboard_wizard:
            keyboard_wizard = keyboard_wizard[0]
        else:
            keyboard_wizard = self.me

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
