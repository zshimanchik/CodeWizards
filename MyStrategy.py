from collections import namedtuple, deque
from itertools import chain

from model.ActionType import ActionType
from model.Faction import Faction
from model.Game import Game
from model.Move import Move
from model.Wizard import Wizard
from model.World import World
from model.Building import Building
import math
import random


try:
    from debug_client import DebugClient
except:
    debug = None
else:
    debug = DebugClient()
debug = False


Vec = namedtuple('Vec', ['x', 'y'])
LINES_PADDING = 500
ON_LINE_DISTANCE = 300
LIFE_THRESHOLD_FOR_SAVING = 50
FARM_POINT_OFFSET = 50  # must be less than ON_LINE_DISTANCE
LIFE_REGEN_OFFSET = 400
TARGET_DISTANCE_TO_STAY = 50

STRAFE_OBJECT_MAX_DISTANCE = 200
NEAREST_RADIUS = 600  # equals to wizard vision range
MATRIX_CELL_SIZE = 40
MATRIX_CELL_AMOUNT = int(NEAREST_RADIUS * 2 / MATRIX_CELL_SIZE)
BATTLE_SPEED = 3


class MoveState:
    STAYING = 'staying'
    MOVING_TO_TARGET = 'moving_to_target'
    STACKED = 'stacked'
    STACKED_BACKWARD = 'stacked_backward'


class LineState:
    MOVING_TO_LINE = 'moving_to_line'
    ON_LINE = 'on_line'


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


class MyStrategy:
    GOTO = None
    look_at = Vec(0, 3200)

    plan = deque([Vec(250, 3400)])
    unstack_moving = 0
    unstack_strafe_direction = 1
    move_state = MoveState.STAYING
    matrix = [[0] * MATRIX_CELL_AMOUNT for _ in range(MATRIX_CELL_AMOUNT)]


    def __init__(self):
        self.line_state = LineState.MOVING_TO_LINE
        self._reset_lists()
        self._reset_cached_values()
        self.tick = 0

    def move(self, me: Wizard, world: World, game: Game, move: Move):
        self.me = me
        self.world = world
        self.game = game
        self.move_obj = move
        self.update_analyzing()

        self._derive_nearest()

        self._check_state()
        if self.GOTO:  # debug purpose to check battle_goto or goto algorithms
            self.battle_goto(self.GOTO, self.look_at)
        else:
            self.update()

        self.tick +=1

        if debug:
            with debug.pre() as dbg:
                matrix_top = self.me.y - MATRIX_CELL_SIZE * MATRIX_CELL_AMOUNT/2
                matrix_left = self.me.x - MATRIX_CELL_SIZE * MATRIX_CELL_AMOUNT/2
                for row, row_value in enumerate(self.matrix):
                    for col, value in enumerate(row_value):
                        if value == 0:
                            color = (0.9, 0.9, 0.9)
                        elif value == 666:
                            color = (0.9, 0.6, 0.6)
                        elif value > 0:
                            color_value = min(0.9, value / 30)
                            color = (0.9-color_value, 0.9, 0.9-color_value)
                        else:
                            color = (0.8, 0.8, 1)
                        dbg.fill_rect(
                            matrix_left + col * MATRIX_CELL_SIZE + 1,
                            matrix_top + row * MATRIX_CELL_SIZE + 1,
                            matrix_left + (col+1) * MATRIX_CELL_SIZE - 1,
                            matrix_top + (row+1) * MATRIX_CELL_SIZE - 1,
                            color
                        )
            with debug.abs() as dbg:
                text = []
                text.append('{:.0f}, {:.0f}'.format(self.me.x, self.me.y))
                text.append(str(self.move_state))
                text.append(str(self.line_state))
                for i, line in enumerate(text):
                    dbg.text(600, 300+i*14, line, (1, 0, 0))

    def _derive_nearest(self):
        self.nearest_objects = []
        self.enemies_in_cast_range = []
        self.matrix = [[0]* MATRIX_CELL_AMOUNT for _ in range(MATRIX_CELL_AMOUNT)]
        matrix_top = self.me.y - MATRIX_CELL_SIZE * MATRIX_CELL_AMOUNT/2
        matrix_left = self.me.x - MATRIX_CELL_SIZE * MATRIX_CELL_AMOUNT/2
        for obj in chain(self.world.buildings, self.world.minions, self.world.wizards, self.world.trees):
            obj.distance = distance(self.me, obj)
            if obj.distance <= NEAREST_RADIUS and obj.id != self.me.id:
                self.nearest_objects.append(obj)
            if self._is_enemy(obj) and obj.distance <= self.game.wizard_cast_range:
                self.enemies_in_cast_range.append(obj)

            col_left = int((obj.x - obj.radius - matrix_left) // MATRIX_CELL_SIZE)
            col_right = int((obj.x + obj.radius - matrix_left) // MATRIX_CELL_SIZE)
            row_top = int((obj.y - obj.radius - matrix_top) // MATRIX_CELL_SIZE)
            row_bottom = int((obj.y + obj.radius - matrix_top) // MATRIX_CELL_SIZE)

            for row in range(row_top, row_bottom + 1):
                for col in range(col_left, col_right + 1):
                    if 0 <= col < MATRIX_CELL_AMOUNT and 0 <= row < MATRIX_CELL_AMOUNT:
                        self.matrix[row][col] = -1

    def _check_state(self):
        if distance(self.me, self.top_line_bound) < ON_LINE_DISTANCE:
            new_state = LineState.ON_LINE
        else:
            new_state = LineState.MOVING_TO_LINE

        if self.line_state != new_state:
            old_state = self.line_state
            self.line_state = new_state
            self._line_state_changed(old_state)

    def _line_state_changed(self, old_state):
        pass

    def update(self):
        if self.line_state == LineState.MOVING_TO_LINE:
            move_target = self._build_path_to_farm_point()
            self.goto(move_target)
        elif self.line_state == LineState.ON_LINE:
            self._on_line_update()

    def _on_line_update(self):
        enemy = self._choice_enemy_to_shoot()
        if enemy:
            self.move_obj.action = ActionType.MAGIC_MISSILE
            self.move_obj.min_cast_distance = enemy.distance - enemy.radius
            look_at = enemy
        else:
            look_at = self.top_line_enemy_center_of_mass
        stay_at = self.farm_point
        self.battle_goto_smart(stay_at, look_at)
        # self.battle_goto(stay_at, look_at)

    def battle_goto_smart(self, target, look_at):

        if debug:
            with debug.post() as dbg:
                dbg.fill_circle(target.x, target.y, 10, (0,0,1))
        if distance(self.me, target) < 1.42 * MATRIX_CELL_SIZE:
            return self.battle_goto(target, look_at)

        shifted_target = Vec(target.x - MATRIX_CELL_SIZE / 2, target.y - MATRIX_CELL_SIZE / 2)
        matrix_top = self.me.y - MATRIX_CELL_SIZE * MATRIX_CELL_AMOUNT / 2
        matrix_left = self.me.x - MATRIX_CELL_SIZE * MATRIX_CELL_AMOUNT / 2
        target_row = int((shifted_target.y - matrix_top) / MATRIX_CELL_SIZE)
        target_col = int((shifted_target.x - matrix_left) / MATRIX_CELL_SIZE)
        me_row = me_col = int(MATRIX_CELL_AMOUNT / 2) -1
        self.matrix[me_row][me_col] = 1
        self.matrix[me_row+1][me_col] = 0
        self.matrix[me_row+1][me_col+1] = 0
        self.matrix[me_row][me_col+1] = 0

        queue = deque()
        queue.append((me_row, me_col))
        stop = False
        while queue and not stop:
            cur_row, cur_col = queue.popleft()
            path_length = self.matrix[cur_row][cur_col] + 1
            for drow, dcol in ((-1, 0), (0, 1), (1, 0), (0, -1)):
                row = cur_row - drow
                col = cur_col - dcol
                if 0 <= row < MATRIX_CELL_AMOUNT - 1 and 0 <= col < MATRIX_CELL_AMOUNT - 1 and self.empty(row, col) \
                        and (self.matrix[row][col] == 0 or self.matrix[row][col] > path_length):
                    self.matrix[row][col] = path_length
                    queue.append((row, col))
                    if row == target_row and col == target_col:
                        stop = True
                        break

        if self.matrix[target_row][target_col] <= 0:
            visited = set()
            visited.add((target_row, target_col))
            queue = deque()
            queue.append((target_row, target_col))
            stop = False
            while not stop:
                cur_row, cur_col = queue.popleft()
                for drow, dcol in ((-1, 0), (0, 1), (1, 0), (0, -1)):
                    row = cur_row - drow
                    col = cur_col - dcol
                    row_col = (row, col)
                    if 0 <= row < MATRIX_CELL_AMOUNT - 1 and 0 <= col < MATRIX_CELL_AMOUNT - 1 and row_col not in visited:
                        if self.matrix[row][col] > 0:
                            target_row, target_col = row, col
                            stop = True
                            break
                        visited.add(row_col)
                        queue.append(row_col)

        path = []

        cur_row, cur_col = target_row, target_col
        path_length = self.matrix[target_row][target_col] - 1
        while (cur_row, cur_col) != (me_row, me_col):
            for drow, dcol in ((-1, 0), (0, 1), (1, 0), (0, -1)):
                row = cur_row - drow
                col = cur_col - dcol
                if 0 <= row < MATRIX_CELL_AMOUNT - 1 and 0 <= col < MATRIX_CELL_AMOUNT - 1 \
                        and self.matrix[row][col] == path_length:
                    path.append((row, col))
                    cur_row, cur_col = row, col
                    path_length -= 1
                    break

        for row, col in path:
            self.matrix[row][col] = 666

        if len(path) == 0:
            return self.battle_goto(target, look_at)
        elif len(path) > 1:
            row, col = path[-2]
        else:
            row, col = path[-1]
        target = Vec(matrix_left + (col+1) * MATRIX_CELL_SIZE, matrix_top + (row+1) * MATRIX_CELL_SIZE)
        if debug:
            with debug.abs() as dbg:
                dbg.text(400, 250, 'smart', (1, 0,0))
        self.battle_goto(target, look_at)



    def empty(self, row_start, col_start):
        row_end = row_start+1
        col_end = col_start+1
        for row in range(row_start, row_end+1):
            for col in range(col_start, col_end+1):
                if self.matrix[row][col] < 0:
                    return False
        return True

    def battle_goto(self, target, look_at):
        if debug:
            with debug.post() as dbg:
                dbg.fill_circle(target.x, target.y, 5, (1,0,1))
                # dbg.fill_circle(look_at.x, look_at.y, 10, (0,0,1))
        v = Vec(target.x - self.me.x, target.y - self.me.y)
        l = math.hypot(v.x, v.y)
        if l == 0:
            return

        v = Vec(v.x/l, v.y/l)
        ca = math.cos(-self.me.angle)
        sa = math.sin(-self.me.angle)
        v = Vec(ca*v.x - sa*v.y, sa*v.x + ca*v.y)
        self.move_obj.speed = v.x * BATTLE_SPEED
        self.move_obj.strafe_speed = v.y * BATTLE_SPEED

        turn = self.me.get_angle_to_unit(look_at)
        self.move_obj.turn = turn

    def _choice_enemy_to_shoot(self):
        best_enemy = min(
            self.enemies_in_cast_range,
            key=lambda x: x.life + isinstance(x, Wizard) * (-2000) + isinstance(x, Building) * (-1000),
            default=None
        )
        return best_enemy

    def goto(self, target: Vec):
        if debug:
            with debug.post() as dbg:
                dbg.fill_circle(target.x, target.y, 10, (1,0,1))
                dbg.line(self.me.x, self.me.y, target.x, target.y, (1,0,1))

        if self._check_if_stacked():
            return

        if distance(self.me, target) < TARGET_DISTANCE_TO_STAY:
            self.move_state = MoveState.STAYING
            return
        else:
            self.move_state = MoveState.MOVING_TO_TARGET

        self.move_obj.speed = self.game.wizard_forward_speed
        angle = self.me.get_angle_to_unit(target)
        self.move_obj.turn = angle
        vec = Vec(target.x - self.me.x, target.y - self.me.y)
        self.move_obj.strafe_speed = self._calc_strafe(vec)

    def _check_if_stacked(self):
        if self.move_state == MoveState.MOVING_TO_TARGET and self.me.speed_x == self.me.speed_y == 0:
            self.move_state = MoveState.STACKED
            self.unstack_strafe_direction = random.choice([-1, 1])
            self.unstack_moving = random.randint(7, 20)
            self._move_to_unstack()
            return True

        if self.move_state == MoveState.STACKED and self.me.speed_x == self.me.speed_y == 0:
            self.move_state = MoveState.STACKED_BACKWARD
            self.unstack_strafe_direction = random.choice([-1, 1])
            self.unstack_moving = random.randint(7, 20)
            self._move_to_unstack()
            return True

        if self.unstack_moving > 0:
            self._move_to_unstack()
            self.unstack_moving -= 1
            return True
        return False

    def _move_to_unstack(self):
        self.move_obj.action = ActionType.MAGIC_MISSILE
        if self.move_state == MoveState.STACKED:
            self.move_obj.speed = -self.game.wizard_backward_speed
            self.move_obj.strafe_speed = math.copysign(self.game.wizard_strafe_speed, self.unstack_strafe_direction)

        if self.move_state == MoveState.STACKED_BACKWARD:
            self.move_obj.speed = self.game.wizard_forward_speed / 2
            self.move_obj.turn = self.game.wizard_max_turn_angle
            self.move_obj.strafe_speed = math.copysign(self.game.wizard_strafe_speed, self.unstack_strafe_direction)

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

    def _build_path_to_farm_point(self):
        fp = self.farm_point
        if self.me.y > self.world.height-700:
            return Vec(LINES_PADDING/2, self.world.height-800)
        if self.me.y > LINES_PADDING and self.me.x > LINES_PADDING:
            if fp.x <= LINES_PADDING or self.me.x < self.me.y:
                return Vec(LINES_PADDING/2, self.me.y)
            else:
                return Vec(self.me.x, LINES_PADDING/2)
        if fp.x < LINES_PADDING:
            return fp
        if self.me.y > LINES_PADDING:
            return Vec(LINES_PADDING/2, LINES_PADDING/2)
        else:
            return fp

    def _is_enemy(self, obj):
        return opposite_faction(self.me.faction) == obj.faction

    def _reset_lists(self):
        self.top_line = []
        self.middle_line = []
        self.bottom_line = []
        self.top_line_enemies = []
        self.top_line_allies = []

    def update_analyzing(self):
        self._reset_cached_values()
        self._reset_lists()
        for minion in chain(self.world.minions, self.world.buildings, self.world.wizards):
            if minion.x < LINES_PADDING or minion.y < LINES_PADDING:
                self.top_line.append(minion)
                if minion.faction == self.me.faction:
                    self.top_line_allies.append(minion)
                elif minion.faction == opposite_faction(self.me.faction):
                    self.top_line_enemies.append(minion)
            elif minion.y > self.world.height - LINES_PADDING or minion.x > self.world.width - LINES_PADDING:
                self.bottom_line.append(minion)
            else:
                self.middle_line.append(minion)

    def _reset_cached_values(self):
        self._top_bound = None
        self._top_enemy_center = None
        self._farm_point = None

    @property
    def top_line_bound(self):
        if self._top_bound is None:
            self._top_bound = self._get_top_line_bound()
        return self._top_bound

    @property
    def farm_point(self):
        if self._farm_point is None:
            self._farm_point = self._calc_farm_point()
        return self._farm_point

    @property
    def top_line_enemy_center_of_mass(self):
        if self._top_enemy_center is None:
            self._top_enemy_center = self._get_top_line_enemy_center_of_mass(self.top_line_enemies)
        return self._top_enemy_center

    def _get_top_line_bound(self):
        x, y = LINES_PADDING / 2, self.world.height - LINES_PADDING / 2
        for minion in self.top_line_allies:
            if minion.y < LINES_PADDING:
                if y > LINES_PADDING or minion.x > x :
                    x = minion.x
                    y = LINES_PADDING / 2
            else:
                if minion.y < y:
                    x = LINES_PADDING / 2
                    y = minion.y
        return self._get_center_of_mass(Vec(x, y), self.top_line_allies)

    def _get_center_of_mass(self, bound_point:Vec, line):
        RADIUS_AROUND_BOUND = 400
        x_sum, y_sum = 0, 0
        count = 0
        for minion in line:
            if math.sqrt((bound_point.x - minion.x)**2 + (bound_point.y - minion.y)**2) < RADIUS_AROUND_BOUND:
                x_sum += minion.x
                y_sum += minion.y
                count += 1
        return Vec(x_sum/count, y_sum/count) if count else bound_point

    def _get_top_line_enemy_center_of_mass(self, line):
        x_sum, y_sum = 0, 0
        count = 0
        for minion in line:
            x_sum += minion.x
            y_sum += minion.y
            count += 1
        if count == 0:
            return self.top_line_bound
        else:
            return Vec(x_sum/count, y_sum/count)

    def get_farm_point_with_offset(self, offset):
        top = self.top_line_bound
        if top.x >= LINES_PADDING:
            point = Vec(max(0, top.x - offset), LINES_PADDING / 2)
            if point.x < LINES_PADDING/2:
                return Vec(LINES_PADDING /2, LINES_PADDING - point.x)
            else:
                return point
        else:
            return Vec(LINES_PADDING / 2, min(self.world.height-300, top.y + offset))

    def _calc_farm_point(self):
        if self.me.life < LIFE_THRESHOLD_FOR_SAVING:
            return self.get_farm_point_with_offset(LIFE_REGEN_OFFSET)
        else:
            return self.get_farm_point_with_offset(FARM_POINT_OFFSET)



def opposite_faction(faction):
    return Faction.RENEGADES if faction == Faction.ACADEMY else Faction.ACADEMY



