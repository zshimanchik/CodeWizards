
class Vec:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f'Vec({self.x:.2f}, {self.y:.2f})'


class MoveState:
    STAYING = 'staying'
    MOVING_TO_TARGET = 'moving_to_target'
    STACKED = 'stacked'
    STACKED_BACKWARD = 'stacked_backward'


class LineState:
    MOVING_TO_LINE = 'moving_to_line'
    ON_LINE = 'on_line'
