import sys, os
sys.path.insert(0, os.path.abspath('..'))

from kivy.graphics import Color, Line
from kivy.graphics.instructions import InstructionGroup

class BlockGUI(InstructionGroup):
    def __init__(self, norm, pos):
        super(BlockGUI, self).__init__()

        self.norm = norm
        self.pos = pos
        self.size = self.norm.nt((50, 50))

        self.add(Color(1, 1, 1))
        self.add(Line(rectangle=(*self.pos, *self.size), width=2))
