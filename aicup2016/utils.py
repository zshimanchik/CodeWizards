import math

from aicup2016.models import Vec
from model.Faction import Faction


def cached_property(func):
    @property
    def wrapper(self):
        storage = self.__dict__.setdefault('__cached_properties', dict())
        if func.__name__ not in storage:
            storage[func.__name__] = func(self)
        return storage[func.__name__]
    return wrapper


def distance(*args):
    """
    x1, y1, x2, y2 -> distance
    obj1, obj2 -> distance
    obj1, obj2 must have x,y attributes
    """
    if len(args) == 4:
        return math.hypot(args[0] - args[2], args[1] - args[3])
    if len(args) == 2:
        return math.hypot(args[0].x - args[1].x, args[0].y - args[1].y)
    raise TypeError("distance take exactly 2 or 4 arguments")


def distance2(*args):
    """
    x1, y1, x2, y2 -> distance
    obj1, obj2 -> distance
    obj1, obj2 must have x,y attributes
    """
    if len(args) == 4:
        return (args[0] - args[2]) ** 2 + (args[1] - args[3]) ** 2
    if len(args) == 2:
        return (args[0].x - args[1].x) ** 2 + (args[0].y - args[1].y) ** 2
    raise TypeError("distance take exactly 2 or 4 arguments")


def opposite_faction(faction):
    return Faction.RENEGADES if faction == Faction.ACADEMY else Faction.ACADEMY


def get_units_in_radius(units, point, radius):
    for unit in units:
        if distance(unit, point) < radius:
            yield unit


def center_of_mass(units):
    x_sum, y_sum = 0, 0
    count = 0
    for unit in units:
        x_sum += unit.x
        y_sum += unit.y
        count += 1

    if count == 0:
        return None
    else:
        return Vec(x_sum / count, y_sum / count)
