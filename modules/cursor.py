import sys, os
sys.path.insert(0, os.path.abspath('..'))

from common.clock import Clock, SimpleTempoMap, tick_str, kTicksPerQuarter
from common.gfxutil import CEllipse, AnimGroup
from kivy.graphics import Color, Line, Rectangle
from kivy.graphics import PushMatrix, PopMatrix, Rotate, Translate
from kivy.graphics.instructions import InstructionGroup

from modules.cursor_gui import CursorGUI

class TempoCursor(InstructionGroup):
    """
    This module is a timed cursor that creates touch_down events on any objects that it is placed
    over. It uses an underlying tempo that is room-wide.
    """
    name = 'TempoCursor'

    def __init__(self, norm, pos, tempo, clock, tempo_map):
        super(TempoCursor, self).__init__()
        self.norm = norm

        self.cursor_color = Color(1, 1, 1)
        self.time_color = Color(159/255, 187/255, 208/255) # blue

        self.cursor = CEllipse(cpos=pos, csize=self.norm.nt((70, 70)))
        self.add(self.cursor_color)
        self.add(self.cursor)

        self.tempo = tempo
        self.clock = clock
        self.tempo_map = tempo_map

        self.add(PushMatrix())
        self.add(Translate(*pos))
        self.time_marker = Line(points=(0, 0, 0, self.norm.nv(30)), width=3)
        self.rotate = Rotate(angle=0)
        self.add(self.rotate)
        self.add(self.time_color)
        self.add(self.time_marker)
        self.add(PopMatrix())

        self.on_update(0)

    def on_update(self, dt):
        cur_time = self.clock.get_time()
        cur_tick = self.tempo_map.time_to_tick(cur_time)
        angle = (360 * (cur_tick / (kTicksPerQuarter * 4))) % 360
        self.rotate.angle = -angle

class TempoCursorHandler(object):
    """
    Handles the TempoCursor GUI.
    Also stores and updates all currently active TempoCursors.
    """
    def __init__(self, norm, sandbox, mixer, client, client_id, tempo=120):
        self.norm = norm
        self.module_name = 'TempoCursor'
        self.sandbox = sandbox
        self.mixer = mixer
        self.client = client
        self.cid = client_id

        self.tempo = tempo
        self.clock = Clock()
        self.tempo_map = SimpleTempoMap(bpm=self.tempo)

        self.cursors = AnimGroup()
        self.sandbox.add(self.cursors)

        self.gui = CursorGUI(norm, pos=(20, 300))

    def on_touch_down(self, cid, pos):
        if not self.sandbox.in_bounds(pos):
            return

        cursor = TempoCursor(self.norm, pos, self.tempo, self.clock, self.tempo_map)
        self.cursors.add(cursor)

    def on_touch_move(self, cid, pos):
        pass

    def on_touch_up(self, cid, pos):
        pass

    def on_key_down(self, cid, key):
        if key == 'p':
            self.clock.toggle()

    def on_update(self):
        self.cursors.on_update()

    def display_controls(self):
        cur_time = self.clock.get_time()
        cur_tick = self.tempo_map.time_to_tick(cur_time)

        info = 'tempo: {}\n'.format(self.tempo)
        info += 'time: {}\n'.format(cur_time)
        info += tick_str(cur_tick)
        return info
