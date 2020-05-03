import sys, os
sys.path.insert(0, os.path.abspath('..'))

from kivy.graphics import Color, Line, Rectangle
from kivy.graphics.instructions import InstructionGroup

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

class CursorGUI(InstructionGroup):
    def __init__(self, norm, pos, beat_callback):
        super(CursorGUI, self).__init__()

        self.norm = norm
        self.pos = pos
        self.size = self.norm.nt((300, 500))

        self.add(Color(1, 1, 1))
        self.add(Line(rectangle=(*self.pos, *self.size), width=2))

        bs_pos = (self.pos[0] + self.norm.nv(20), self.pos[1] + self.norm.nv(20))
        self.bs = BeatSelect(self.norm, bs_pos, beat_callback)
        self.add(self.bs)

    def on_touch_down(self, pos):
        if in_bounds(pos, self.bs.pos, self.bs.size):
            self.bs.on_touch_down(pos)

class CurrentCursor(InstructionGroup):
    def __init__(self, norm, pos):
        super(CurrentCursor, self).__init__()
        self.norm = norm
        self.pos = pos
        pass

class TempoSelect(InstructionGroup):
    def __init__(self, norm, pos):
        super(TempoSelect, self).__init__()
        self.norm = norm
        self.pos = pos
        pass

class BeatSelect(InstructionGroup):
    def __init__(self, norm, pos, callback):
        super(BeatSelect, self).__init__()

        self.norm = norm
        self.pos = pos
        self.callback = callback

        self.margin = self.norm.nv(20)
        self.beat_margin = self.norm.nv(5)
        self.beat_size = self.norm.nt((50, 50))
        self.size = (
            2*self.margin + 4*self.beat_size[0] + 3*self.beat_margin,
            2*self.margin + 4*self.beat_size[0] + 3*self.beat_margin
        )

        self.border = Line(rectangle=(*self.pos, *self.size), width=2)
        self.border_color = Color(238/255, 234/255, 202/255) # yellow
        self.add(self.border_color)
        self.add(self.border)

        self.touch_points = []
        self.matrix = [[None for _ in range(4)] for _ in range(4)]
        self.color_matrix = [[Color(1, 1, 1) for _ in range(4)] for _ in range(4)]
        start_pos = (self.pos[0] + self.margin, self.pos[1] + self.margin)
        unit = self.beat_size[0] + self.beat_margin
        for i in range(4):
            for j in range(4):
                beat = Rectangle(
                    pos=(start_pos[0] + i*unit, start_pos[1] + j*unit), size=self.beat_size
                )
                self.matrix[i][j] = beat
                self.add(self.color_matrix[i][j])
                self.add(beat)

    def pos_to_beat(self, pos):
        for i in range(4):
            for j in range(4):
                rect = self.matrix[i][j]
                if in_bounds(pos, rect.pos, rect.size):
                    return (i, j)
        return None, None

    def toggle(self, i, j):
        if self.color_matrix[i][j].rgb == [1.0, 1.0, 1.0]:
            self.color_matrix[i][j].rgb = (144/255, 238/255, 144/255) # green
            self.touch_points.append(4*(3-j) + i)
            self.touch_points = sorted(self.touch_points)
        else:
            self.color_matrix[i][j].rgb = (1, 1, 1)
            self.touch_points.remove(4*(3-j) + i)

    def on_touch_down(self, pos):
        i, j = self.pos_to_beat(pos)
        if i is not None:
            self.toggle(i, j)
            self.callback(self.touch_points)
