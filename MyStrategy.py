from collections import namedtuple, deque
from model.ActionType import ActionType
from model.Faction import Faction
from model.Game import Game
from model.Move import Move
from model.Wizard import Wizard
from model.World import World
import math

Vec = namedtuple('Vec', ['x', 'y'])
LINES_PADDING = 500
ON_LINE_DISTANCE = 400
STRAFE_OBJECT_MAX_DISTANCE = 200


class MoveState:
    STAYING = 0
    MOVING_TO_TARGET = 1
    STACKED = 2
    STACKED_BACKWARD = 3


class LineState:
    MOVING_TO_LINE = 0
    ON_LINE = 1


def distance(*args):
    """
    x1, y1, x2, y2 -> distance
    obj1, obj2 -> distance
    obj1, obj2 must have x,y attributes
    """
    if len(args) == 4:
        return math.sqrt((args[0]-args[2])**2 + (args[1]-args[3])**2)
    if len(args) == 2:
        return math.sqrt((args[0].x - args[1].x)**2 + (args[0].y - args[1].y)**2)
    raise TypeError("distance take exactly 2 or 4 arguments")


class MyStrategy:
    GOTO = Vec(250, 3400)

    plan = deque([Vec(250, 3400)])
    unstack_moving = 0
    move_state = MoveState.STAYING


    def __init__(self):
        self.line_state = LineState.MOVING_TO_LINE
        self.analyzer = Analyzer()

    def move(self, me: Wizard, world: World, game: Game, move: Move):
        self.me = me
        self.world = world
        self.game = game
        self.move_obj = move
        self.analyzer.update(self.world)

        # move.action = ActionType.MAGIC_MISSILE
        self._derive_nearest()

        self.next_goto()
        # if self.GOTO:
        #     self.goto(self.GOTO)

    def _derive_nearest(self, radius=600):
        self.nearest_objects = []
        for obj in self.world.buildings + self.world.minions + self.world.wizards + self.world.trees:
            obj.distance = math.sqrt((self.me.x-obj.x)**2 + (self.me.y-obj.y)**2)
            if obj.distance <= radius and obj.id != self.me.id:
                self.nearest_objects.append(obj)

    def _check_state(self):
        if distance(self.me, self.analyzer.top_line_bound) < ON_LINE_DISTANCE:
            new_state = LineState.ON_LINE
        else:
            new_state = LineState.MOVING_TO_LINE

        if self.line_state != new_state:
            old_state = self.line_state
            self.line_state = new_state
            self._line_state_changed(old_state)

    def _line_state_changed(self, old_state):
        pass


    def next_goto(self):
        if self.line_state == LineState.MOVING_TO_LINE:
            move_target = self._calc_farm_point()
            # self.goto(move_target)
            self.goto(self.GOTO)
        elif self.line_state == LineState.ON_LINE:
            self.move_state = MoveState.STAYING


        # if self.GOTO is None and not self.plan:
        #     # self.plan.append(self.analyzer.top_bound)
        #     self.GOTO = self._calc_farm_point()
        #     # self.GOTO = self.plan.popleft()
        #
        # if self.GOTO is None or math.sqrt((self.GOTO.x - self.me.x)**2 + (self.GOTO.y - self.me.y)**2) < 30:
        #     self.GOTO = self.plan.popleft() if len(self.plan) else None
        #
        # if self.GOTO is None and not self.plan:
        #     self.move_state = MoveState.STAYING

    def _calc_farm_point(self):
        DIST = 200
        top = self.analyzer.top_line_bound
        if top.x >= LINES_PADDING:
            return Vec(max(0, top.x - DIST), LINES_PADDING / 2)
        else:
            return Vec(LINES_PADDING / 2, min(self.world.height, top.y + DIST))






    def goto(self, target: Vec):
        if self._check_if_stacked():
            return

        self.move_state = MoveState.MOVING_TO_TARGET

        self.move_obj.speed = self.game.wizard_forward_speed
        vec = Vec(target.x - self.me.x, target.y - self.me.y)
        self.move_obj.turn = self._calc_turn_angle(vec)
        self.move_obj.strafe_speed = self._calc_strafe(vec)

    def _check_if_stacked(self):
        if self.move_state == MoveState.MOVING_TO_TARGET and self.me.speed_x == self.me.speed_y == 0:
            self.move_state = MoveState.STACKED
            self.unstack_moving = 10
            self._move_to_unstack()
            return True

        if self.move_state == MoveState.STACKED and self.me.speed_x == self.me.speed_y == 0:
            self.move_state = MoveState.STACKED_BACKWARD
            self.unstack_moving = 10
            self._move_to_unstack()
            return True

        if self.unstack_moving > 0:
            self._move_to_unstack()
            self.unstack_moving -= 1
            return True
        return False

    def _move_to_unstack(self):
        if self.move_state == MoveState.STACKED:
            self.move_obj.speed = -self.game.wizard_backward_speed

        if self.move_state == MoveState.STACKED_BACKWARD:
            self.move_obj.speed = self.game.wizard_forward_speed / 2
            self.move_obj.turn = self.game.wizard_max_turn_angle

        self.unstack_moving -= 1



    def _calc_turn_angle(self, vec: Vec):
        angle = math.atan2(vec.y, vec.x)
        turn = angle - self.me.angle
        turn = min(self.game.wizard_max_turn_angle, turn)
        turn = max(-self.game.wizard_max_turn_angle, turn)
        return turn

    def _calc_strafe(self, vec: Vec):
        obj = self._get_closest_strafe_object()
        if obj:
            a = vec.y
            b = -vec.x
            c = (self.me.x - obj.x) * (-vec.y) + (self.me.y - obj.y) * vec.x

            x0 = - (a * c) / (a ** 2 + b ** 2)
            y0 = - (b * c) / (a ** 2 + b ** 2)
            if math.sqrt(x0 ** 2 + y0 ** 2) <= obj.radius + self.me.radius:
                if vec.y > 0:
                    if x0 < 0:
                        sign = 1
                    else:
                        sign = -1
                else:
                    if x0 < 0:
                        sign = -1
                    else:
                        sign = 1
                return self.game.wizard_strafe_speed * sign
        return 0

    def _get_closest_strafe_object(self):
        closest_obj = None
        for obj in self.nearest_objects:
            d_angle = self._delta_angle_to(obj)
            if abs(d_angle) <= math.pi/2 and obj.distance < STRAFE_OBJECT_MAX_DISTANCE \
                    and (closest_obj is None or obj.distance < closest_obj.distance):
                closest_obj = obj
        return closest_obj

    def _delta_angle_to(self, obj):
        angle = math.atan2(obj.y - self.me.y, obj.x - self.me.x)
        d_angle = self.me.angle - angle
        if d_angle > math.pi:
            d_angle -= math.pi*2
        if d_angle < -math.pi:
            d_angle += math.pi*2
        return d_angle


class Analyzer(object):

    def __init__(self):
        self.top_line = []
        self.middle_line = []
        self.bottom_line = []
        self._reset_cached_values()

    def update(self, world):
        self._reset_cached_values()
        self.top_line = []
        self.middle_line = []
        self.bottom_line = []
        self.world = world
        for minion in world.minions + world.buildings:
            if minion.x < LINES_PADDING or minion.y < LINES_PADDING:
                self.top_line.append(minion)
            elif minion.y > world.height - LINES_PADDING or minion.x > world.width - LINES_PADDING:
                self.bottom_line.append(minion)
            else:
                self.middle_line.append(minion)


    def _reset_cached_values(self):
        self._top_bound = None
        self._top_enemy_center = None



    @property
    def top_line_bound(self):
        if self._top_bound is None:
            self._top_bound = self._get_top_line_bound()
        return self._top_bound


    def _get_top_line_bound(self):
        x, y = LINES_PADDING / 2, self.world.height - LINES_PADDING / 2
        for minion in self.top_line:
            if minion.faction != Faction.ACADEMY:
                continue
            if minion.y < LINES_PADDING:
                if y > LINES_PADDING or minion.x > x :
                    x = minion.x
                    y = LINES_PADDING / 2
            else:
                if minion.y < y:
                    x = LINES_PADDING / 2
                    y = minion.y
        return self._get_center_of_mass(Vec(x, y), self.top_line)

    def _get_center_of_mass(self, bound_point:Vec, line):
        RADIUS_AROUND_BOUND = 400
        x_sum, y_sum = 0, 0
        count = 0
        for minion in line:
            if minion.faction != Faction.ACADEMY:
                continue
            if math.sqrt((bound_point.x - minion.x)**2 + (bound_point.y - minion.y)**2) < RADIUS_AROUND_BOUND:
                x_sum += minion.x
                y_sum += minion.y
                count += 1
        return Vec(x_sum/count, y_sum/count)

    @property
    def top_line_enemy_center_of_mass(self):
        if self._top_enemy_center is None:
            self._top_enemy_center = self._get_top_line_enemy_center_of_mass(self.top_line)
        return self._top_enemy_center

    def _get_top_line_enemy_center_of_mass(self, line):
        x_sum, y_sum = 0, 0
        count = 0
        for minion in line:
            if minion.faction != Faction.RENEGADES:
                continue
            x_sum += minion.x
            y_sum += minion.y
            count += 1
        if count == 0:
            return self.top_line_bound
        else:
            return Vec(x_sum/count, y_sum/count)







