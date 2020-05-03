import copy, math
import sys, os
sys.path.insert(0, os.path.abspath('..'))

from common.clock import Clock, SimpleTempoMap, Scheduler
from common.clock import tick_str, kTicksPerQuarter, quantize_tick_up
from common.gfxutil import CEllipse, AnimGroup
from kivy.graphics import Color, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix, Rotate, Translate
from kivy.graphics.instructions import InstructionGroup

from modules.cursor_gui import CursorGUI

def in_bounds(mouse_pos, obj_pos, obj_size):
    """
    Check if a mouse's position is inside an object.
    :param mouse_pos: (x, y) mouse position
    :param obj_pos: (x, y) object position
    :param obj_size: (width, height) object size
    """
    return (mouse_pos[0] >= obj_pos[0]) and \
           (mouse_pos[0] <= obj_pos[0] + obj_size[0]) and \
           (mouse_pos[1] >= obj_pos[1]) and \
           (mouse_pos[1] <= obj_pos[1] + obj_size[1])

class TempoCursor(InstructionGroup):
    """
    This module is a timed cursor that creates touch_down events on any objects that it is placed
    over. It uses an underlying tempo that is room-wide.
    """
    name = 'TempoCursor'

    def __init__(self, norm, pos, tempo, clock, tempo_map, touch_points, block_handler):
        super(TempoCursor, self).__init__()
        self.norm = norm
        self.pos = pos
        self.size = self.norm.nt((70, 70))

        self.cursor = CEllipse(cpos=pos, csize=self.size)
        self.add(Color(1, 1, 1))
        self.add(self.cursor)

        self.tempo = tempo
        self.clock = clock
        self.tempo_map = tempo_map
        self.sched = Scheduler(self.clock, self.tempo_map)

        self.block_handler = block_handler

        # 0..15, for 16th note granularity
        self.touch_points = touch_points
        self.index = 0

        # add touch markers
        self.add(PushMatrix())
        self.add(Translate(*pos))
        for touch_point in self.touch_points:
            self.add(Rotate(angle = -360 * touch_point / 16))
            self.add(Color(159/255, 187/255, 208/255)) # blue
            self.add(Line(points=(0, 0, 0, self.norm.nv(25)), width=2))
            self.add(Rotate(angle = 360 * touch_point / 16))
        self.add(PopMatrix())

        # add current time marker
        self.add(PushMatrix())
        self.add(Translate(*pos))
        self.time_marker = Line(points=(0, 0, 0, self.norm.nv(30)), width=3)
        self.rotate = Rotate(angle=0)
        self.add(self.rotate)
        self.add(Color(0, 0, 0))
        self.add(self.time_marker)
        self.add(PopMatrix())

        self.on_update(0)

        cur_tick = self.sched.get_tick()
        next_tick = quantize_tick_up(cur_tick, kTicksPerQuarter * 4)
        next_tick += self.calculate_tick_interval(0, self.touch_points[0])
        self.sched.post_at_tick(self.touch_down, next_tick)

    def on_update(self, dt):
        self.sched.on_update()

        cur_time = self.sched.get_time()
        cur_tick = self.sched.get_tick()
        angle = (360 * (cur_tick / (kTicksPerQuarter * 4))) % 360
        self.rotate.angle = -angle

    def calculate_tick_interval(self, p1, p2):
        if p2 > p1:
            return (p2 - p1)/4 * kTicksPerQuarter
        elif p1 > p2:
            return (p2 + 16 - p1)/4 * kTicksPerQuarter
        else:
            return 0

    def round_to_sixteenth(self, tick):
        kTicksPerSixteenth = kTicksPerQuarter / 4
        kTicksPerMeasure = kTicksPerQuarter * 4
        measure = math.floor(tick / kTicksPerMeasure)
        beat = round(16 * ((tick % kTicksPerMeasure) / kTicksPerMeasure))
        return measure * kTicksPerMeasure + (beat * kTicksPerSixteenth)

    def touch_down(self, tick):
        self._touch_down()

        cur_tick = self.round_to_sixteenth(self.sched.get_tick())
        next_index = (self.index + 1) % len(self.touch_points)
        p1 = self.touch_points[self.index]
        p2 = self.touch_points[next_index]
        interval = kTicksPerQuarter * 4 if len(self.touch_points) == 1 \
              else self.calculate_tick_interval(p1, p2)
        next_tick = cur_tick + interval

        self.index = next_index

        self.sched.post_at_tick(self.touch_down, next_tick)

    def _touch_down(self):
        for block in self.block_handler.blocks.objects:
            if in_bounds(self.pos, block.pos, block.size):
                block.flash()

class TempoCursorHandler(object):
    """
    Handles the TempoCursor GUI.
    Also stores and updates all currently active TempoCursors.
    """
    def __init__(self, norm, sandbox, mixer, client, client_id, block_handler, tempo=60):
        self.norm = norm
        self.module_name = 'TempoCursor'
        self.sandbox = sandbox
        self.mixer = mixer
        self.client = client
        self.cid = client_id
        self.block_handler = block_handler

        self.tempo = tempo
        self.clock = Clock()
        self.tempo_map = SimpleTempoMap(bpm=self.tempo)

        self.touch_points = {}

        self.cursors = AnimGroup()
        self.sandbox.add(self.cursors)

        self.gui = CursorGUI(
            norm, pos=self.norm.nt((20, 300)),
            beat_callback=self.update_touch_points
        )

        self.delete_mode = {}

    def on_touch_down(self, cid, pos):
        if cid == self.cid:
            self.gui.on_touch_down(pos)

        if not self.sandbox.in_bounds(pos):
            return

        for cursor in self.cursors.objects:
            cursor_pos = (cursor.pos[0] - cursor.size[0]/2, cursor.pos[1] - cursor.size[1]/2)
            if in_bounds(pos, cursor_pos, cursor.size):
                if self.delete_mode[cid]:
                    self.cursors.objects.remove(cursor)
                    self.cursors.remove(cursor)
                    return

        if self.delete_mode[cid]:
            return

        touch_points = self.touch_points[cid]

        if len(touch_points) == 0:
            return
        cursor = TempoCursor(
            self.norm, pos, self.tempo, self.clock, self.tempo_map,
            copy.deepcopy(touch_points), self.block_handler
        )
        self.cursors.add(cursor)

    def on_touch_move(self, cid, pos):
        pass

    def on_touch_up(self, cid, pos):
        pass

    def on_key_down(self, cid, key):
        if key == 'p':
            self.clock.toggle()
        if key == 'v' and cid == self.cid:
            self.delete_mode[cid] = not self.delete_mode[cid]
            self.update_server_state(post=True)
        if key == 'up':
            self.tempo += 4
            self.tempo_map.set_tempo(self.tempo)
            self.update_server_state(post=True)

    def on_update(self):
        self.cursors.on_update()

    def update_touch_points(self, touch_points):
        self.touch_points[self.cid] = touch_points
        self.update_server_state(post=True)

    def display_controls(self):
        cur_time = self.clock.get_time()
        cur_tick = self.tempo_map.time_to_tick(cur_time)
        info = 'delete mode: {}\n\n'.format(self.delete_mode[self.cid])
        info += 'tempo: {}\n'.format(self.tempo)
        return info

    def update_server_state(self, post=False):
        """Update server state. If post is True, relay this updated state to all clients."""
        state = {
            'touch_points': self.touch_points,
            'delete_mode': self.delete_mode,
            'tempo': self.tempo
        }
        data = {'module': self.module_name, 'cid': self.cid, 'state': state, 'post': post}
        self.client.emit('update_state', data)

    def update_client_state(self, cid, state):
        """Update this handler's state."""
        if cid != self.cid: # this client already updated its own state
            self.touch_points = state['touch_points']
            self.delete_mode = state['delete_mode']
            self.tempo = state['tempo']

    def sync_state(self, state):
        """
        Initial sync with the server's copy of module state.
        """
        self.touch_points = state['touch_points']
        self.delete_mode = state['delete_mode']
        self.tempo = state['tempo']

        # after initial sync, add default values for this client
        self.touch_points[self.cid] = []
        self.delete_mode[self.cid] = False

        # update server with these default values
        # post=True here because we want all other clients' states to update with this client's
        # default values.
        self.update_server_state(post=True)
