import sys, os
sys.path.insert(0, os.path.abspath('..'))

from common.gfxutil import CLabelRect
from kivy.graphics import Color, Line, Rectangle
from kivy.graphics.instructions import InstructionGroup
from kivy.core.image import Image

class TimbreSelect(InstructionGroup):
    """
    Submodule to select the timbre of PhysicsBubble.
    """
    def __init__(self, pos):
        super(TimbreSelect, self).__init__()

        self.pos = pos
        self.margin = 20
        self.button_length = 64
        self.title_height = 50 # height of the word 'timbre'
        self.size = (
            (4 * self.button_length) + (5 * self.margin),
            self.button_length + (2 * self.margin) + self.title_height
        )

        white = (239/255, 226/255, 222/255)
        self.border_color = Color(1, 0, 0) # red
        self.border = Line(rectangle=(*self.pos, *self.size))
        self.add(self.border_color)
        self.add(self.border)

        button_size = (self.button_length, self.button_length)
        self.sine = Rectangle(size=button_size, texture=Image('images/sine.png').texture)
        self.square = Rectangle(size=button_size, texture=Image('images/square.png').texture)
        self.triangle = Rectangle(size=button_size, texture=Image('images/triangle.png').texture)
        self.sawtooth = Rectangle(size=button_size, texture=Image('images/sawtooth.png').texture)

        self.sine_bg = Rectangle(size=button_size)
        self.square_bg = Rectangle(size=button_size)
        self.triangle_bg = Rectangle(size=button_size)
        self.sawtooth_bg = Rectangle(size=button_size)

        self.sine_color = Color(*white)
        self.square_color = Color(*white)
        self.triangle_color = Color(*white)
        self.sawtooth_color = Color(*white)

        x, y = self.pos

        sine_pos = (x + self.margin, y + self.margin)
        self.sine.pos = self.sine_bg.pos = sine_pos
        self.add(self.sine_color)
        self.add(self.sine_bg)
        self.add(self.sine)

        square_pos = (x + 2*self.margin + self.button_length, y + self.margin)
        self.square.pos = self.square_bg.pos = square_pos
        self.add(self.square_color)
        self.add(self.square_bg)
        self.add(self.square)

        triangle_pos = (x + 3*self.margin + 2*self.button_length, y + self.margin)
        self.triangle.pos = self.triangle_bg.pos = triangle_pos
        self.add(self.triangle_color)
        self.add(self.triangle_bg)
        self.add(self.triangle)

        sawtooth_pos = (x + 4*self.margin + 3*self.button_length, y + self.margin)
        self.sawtooth.pos = self.sawtooth_bg.pos = sawtooth_pos
        self.add(self.sawtooth_color)
        self.add(self.sawtooth_bg)
        self.add(self.sawtooth)

        title_pos = (x + self.size[0]/2, y + self.size[1] - self.title_height/2 - self.margin/2)
        self.title = CLabelRect(cpos=title_pos, text='timbre', font_size='18')
        self.add(Color(*white))
        self.add(self.title)
