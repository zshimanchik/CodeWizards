import numpy as np

import constants as c
from model.Minion import Minion
from model.World import World
from utils import distance


class PotentialMap:
    CELL_AMOUNT = 150

    def __init__(self):
        self.initialized = False
        self.CELL_SIZE = 2
        self.HALF_CELL_SIZE = 1


    def initialize(self, strategy):
        self.strategy = strategy
        assert isinstance(self.strategy.world, World)
        assert self.strategy.world.height == self.strategy.world.width
        self.CELL_SIZE = self.strategy.world.width // self.CELL_AMOUNT
        self.HALF_CELL_SIZE = self.CELL_SIZE / 2
        self.initialized = True
        self.build_buildings_map()
        self.build_trees_map()

    def build_buildings_map(self):
        self.buildings_map = np.zeros((self.CELL_AMOUNT, self.CELL_AMOUNT))
        for tower in self.strategy.world.buildings:
            if tower.faction == self.strategy.me.faction:
                self.put_simple(self.buildings_map, tower, c.ALLY_TOWER_FORCE, tower.attack_range - c.ALLY_TOWER_RADIUS_DELTA)
            else:
                self.put_simple(self.buildings_map, tower, c.ENEMY_TOWER_FORCE, tower.attack_range - c.ALLY_TOWER_RADIUS_DELTA)

    def build_trees_map(self):
        self.trees_map = np.zeros((self.CELL_AMOUNT, self.CELL_AMOUNT))
        for tree in self.strategy.world.trees:
            self.put_simple(self.trees_map, tree, c.TREE_FORCE, tree.radius + c.TREE_RADIUS_DELTA)

    def update(self, strategy):
        if not self.initialized:
            self.initialize(strategy)
        self.world = self.strategy.world
        self.map = np.zeros((self.CELL_AMOUNT, self.CELL_AMOUNT))

        for obj in self.strategy.nearest_objects:
            if isinstance(obj, Minion):
                if obj.faction == self.strategy.me.faction:
                    self.put_simple(self.map, obj, -200, 100)
                else:
                    self.put_simple(self.map, obj, -200, 180)

        self.map = self.map + self.buildings_map + self.trees_map

    def put_simple(self, map, pos, force, radius):
        row, col = int(pos.y // self.CELL_SIZE), int(pos.x // self.CELL_SIZE)
        rad = radius // self.CELL_SIZE
        row_min = max(0, int(row - rad))
        col_min = max(0, int(col - rad))

        row_max = min(self.CELL_AMOUNT-1, int(row + rad))
        col_max = min(self.CELL_AMOUNT-1, int(col + rad))

        for row in range(row_min, row_max+1):
            for col in range(col_min, col_max+1):
                x = col * self.CELL_SIZE + self.HALF_CELL_SIZE
                y = row * self.CELL_SIZE + self.HALF_CELL_SIZE
                dist = distance(pos.x, pos.y, x, y)
                if dist < radius:
                    map[row, col] += (radius - dist) / radius * force
