from common.gfxutil import topleft_label, CEllipse
from kivy.graphics import Color
from kivy.graphics.instructions import InstructionGroup

class Bubble(InstructionGroup):
    def __init__(self, cpos):
        super(Bubble, self).__init__()

        self.color = Color(1, 1, 1)
        self.add(self.color)

        self.bubble = CEllipse(cpos=cpos, csize=(50, 50))
        self.add(self.bubble)