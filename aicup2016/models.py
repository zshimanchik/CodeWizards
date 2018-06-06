import math


class Vec:
    def __init__(self, *args):
        if len(args) == 2:
            self.x = args[0]
            self.y = args[1]
        elif len(args) == 1:
            self.x = args[0].x
            self.y = args[0].y
        else:
            raise ValueError('wrong input for Vec')

    def __truediv__(self, other):
        return Vec(self.x / other, self.y / other)

    def __mul__(self, other):
        return Vec(self.x * other, self.y * other)

    def __sub__(self, other):
        return Vec(self.x - other.x, self.y - other.y)

    def __add__(self, other):
        return Vec(self.x + other.x, self.y + other.y)

    def __str__(self):
        return f'Vec({self.x:.2f}, {self.y:.2f})'

    @property
    def length(self):
        return math.hypot(self.x, self.y)

    @property
    def normalized(self):
        return self / self.length


class MoveState:
    STAYING = 'staying'
    MOVING_TO_TARGET = 'moving_to_target'
    STACKED = 'stacked'
    STACKED_BACKWARD = 'stacked_backward'


class LineState:
    MOVING_TO_LINE = 'moving_to_line'
    ON_LINE = 'on_line'


class GoalState:
    FARM = 'farm'
    TAKE_BONUS = 'take_bonus'
