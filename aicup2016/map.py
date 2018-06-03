
class MapPoint:
    def __init__(self, x, y, remoteness):
        self.x = x
        self.y = y
        self.remoteness = remoteness
        self.neighbors = []

class Map:
    WORLD_SIZE = 4000

    def __init__(self):
        self.points = []
        LINE_PADDING = 200

        self.begin = MapPoint(LINE_PADDING, 3800, 0)
        self.enemy_begin = self.mirror_enemy(self.begin)
        self.points.append(self.begin)
        self.points.append(self.enemy_begin)

        top_line = [
            MapPoint(LINE_PADDING, 3300, 0),
            MapPoint(LINE_PADDING, 2800, 0),
            MapPoint(LINE_PADDING, 2300, 0),
            MapPoint(LINE_PADDING, 1800, 0),
            MapPoint(LINE_PADDING, 1300, 0),
            MapPoint(LINE_PADDING, 900, 0),
        ]
        self.bound_line(top_line)

        bot_line = [self.mirror_diag(point) for point in top_line]
        self.bound_line(bot_line)

        enemy_bot_line = [self.mirror_enemy(point) for point in top_line]
        self.bound_line(enemy_bot_line)

        enemy_top_line = [self.mirror_enemy(point) for point in bot_line]
        self.bound_line(enemy_top_line)

        mid_line = [
            MapPoint(600, 3400, 0),
            MapPoint(1000, 3000, 0),
            MapPoint(1400, 2600, 0),
            MapPoint(1700, 2300, 0),
        ]
        self.bound_line(mid_line)

        enemy_mid_line = [self.mirror_enemy(point) for point in mid_line]
        self.bound_line(enemy_mid_line)

        river_top_line = [
            MapPoint(1600, 1600, 0),
            MapPoint(1200, 1200, 0),
            MapPoint(800, 800, 0),
        ]
        river_bot_line = [self.mirror_enemy(point) for point in river_top_line]
        self.bound_line(river_top_line)
        self.bound_line(river_bot_line)
        self.top_bonus = river_top_line[1]
        self.bottom_bonus = river_bot_line[1]

        self.bound_base(self.begin, top_line, mid_line, bot_line)
        self.bound_base(self.enemy_begin, enemy_bot_line, enemy_mid_line, enemy_top_line)

        top_corner_point = MapPoint(500, 500, 0)
        bot_corner_point = self.mirror_enemy(top_corner_point)
        self.points.append(top_corner_point)
        self.points.append(bot_corner_point)

        self.bound_corner(top_corner_point, top_line, river_top_line, enemy_top_line)
        self.bound_corner(bot_corner_point, enemy_bot_line, river_bot_line, bot_line)

        mid_point = MapPoint(2000, 2000, 0)
        self.points.append(mid_point)
        self.bound_mid(mid_point, mid_line, enemy_mid_line, river_top_line, river_bot_line)

        self.top_line = top_line + [top_corner_point] + enemy_top_line
        self.bottom_line = bot_line + [bot_corner_point] + enemy_bot_line
        self.mid_line = mid_line + [mid_point] + enemy_mid_line

    def mirror_diag(self, point):
        return MapPoint(self.WORLD_SIZE - point.y, self.WORLD_SIZE - point.x, point.remoteness)

    def mirror_enemy(self, point):
        return MapPoint(self.WORLD_SIZE - point.x, self.WORLD_SIZE - point.y, 0)

    def bound_line(self, line):
        prev = None
        for p in line:
            self.add_route(p, prev)
            prev = p

    def bound_base(self, base_point, top_line, mid_line, bot_line):
        self.bound(base_point, top_line[0])
        self.bound(base_point, mid_line[0])
        self.bound(base_point, bot_line[0])
        self.bound(top_line[0], mid_line[0])
        self.bound(bot_line[0], mid_line[0])
        self.bound(top_line[0], bot_line[0])

        self.bound(top_line[1], mid_line[0])
        self.bound(bot_line[1], mid_line[0])

        self.bound(top_line[0], mid_line[1])
        self.bound(bot_line[0], mid_line[1])

    def bound_corner(self, corner_point, vertical_line, river_line, horizontal_line):
        self.bound(corner_point, vertical_line[-1])
        self.bound(corner_point, horizontal_line[-1])
        self.bound(corner_point, river_line[-1])
        self.bound(vertical_line[-1], river_line[-1])
        self.bound(horizontal_line[-1], river_line[-1])

    def bound_mid(self, mid_point, mid_line, enemy_mid_line, river_top_line, river_bot_line):
        self.bound(mid_point, mid_line[-1])
        self.bound(mid_point, enemy_mid_line[-1])
        self.bound(mid_point, river_top_line[0])
        self.bound(mid_point, river_bot_line[0])

        self.bound(mid_line[-1], river_top_line[0])
        self.bound(enemy_mid_line[-1], river_top_line[0])

        self.bound(mid_line[-1], river_bot_line[0])
        self.bound(enemy_mid_line[-1], river_bot_line[0])


    def add_route(self, point, prev=None):
        if prev is not None:
            self.bound(point, prev)
        self.points.append(point)

    def bound(self, p1, p2):
        p1.neighbors.append(p2)
        p2.neighbors.append(p1)

    def __iter__(self):
        return iter(self.points)
