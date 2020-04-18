import sys, os
sys.path.insert(0, os.path.abspath('..'))

from common.gfxutil import CLabelRect
from kivy.graphics import Color, Line, Rectangle
from kivy.graphics.instructions import InstructionGroup
from kivy.core.image import Image
from kivy.clock import Clock as kivyClock

class BounceSelect(InstructionGroup):
    """
    Submodule to toggle bounces of PhysicsBubble.
    """
    def __init__(self, pos, callback):
        super(BounceSelect, self).__init__()

        #default bounces
        self.bounces = 5

        # callback is needed to update PhysicsBubbleHandler's state for bounces
        self.callback = callback
        self.pos = pos
        self.right_pos = (self.pos[0]+100, self.pos[1]) #TODO: get rid of magic number
        self.margin = 20
        self.left_center = (self.margin+5, self.pos[1]+15)
        self.right_center = (self.margin+105, self.pos[1]+15)
        self.size = (25,25)

        self.left_off = Rectangle(
            pos=self.pos,
            size=self.size,
            texture=Image('ui/buttons/left_arrow.png').texture
        )
        self.left_on = Rectangle(
            pos=self.pos,
            size=(25,25),
            texture=Image('ui/buttons/left_arrow_clicked.png').texture
        )
        self.right_off = Rectangle(
            pos=self.right_pos,
            size=self.size,
            texture=Image('ui/buttons/right_arrow.png').texture
        )
        self.right_on = Rectangle(
            pos=self.right_pos,
            size=(25,25),
            texture=Image('ui/buttons/right_arrow_clicked.png').texture
        )
        self.add(self.left_off)
        self.add(self.right_off)

    def in_bounds(self, mouse_pos, obj_pos, obj_size):
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

    def on_touch_down(self, pos):
        if self.in_bounds(pos, self.left_off.pos, self.size):
            self.left_press()
        elif self.in_bounds(pos, self.right_off.pos, self.size):
            self.right_press()

    def left_press(self):
        self.bounces-=1
        self.callback(self.bounces)

    def right_press(self):
        self.bounces+=1
        self.callback(self.bounces)

    def left_press_on_anim(self):
        if self.left_on not in self.children:
            self.add(self.left_on)

    def left_press_off_anim(self):
        if self.left_on in self.children:
            self.remove(self.left_on)

    def right_press_on_anim(self):
        if self.right_on not in self.children:
            self.add(self.right_on)

    def right_press_off_anim(self):
        if self.right_on in self.children:
            self.remove(self.right_on)

    def left_press_anim(self, pos):
        if self.in_bounds(pos, self.left_off.pos, self.size):
            self.left_press_on_anim()
        else:
            self.left_press_off_anim()

    def right_press_anim(self, pos):
        if self.in_bounds(pos, self.right_off.pos, self.size):
            self.right_press_on_anim()
        else:
            self.right_press_off_anim()

    def on_update(self, pos):
        self.left_press_anim(pos)
        self.right_press_anim(pos)


class GravitySelect(InstructionGroup):
    """
    Submodule to toggle gravity of PhysicsBubble.
    """
    def __init__(self, pos, callback):
        super(GravitySelect, self).__init__()

        # callback is needed to update PhysicsBubbleHandler's state for timbre
        self.callback = callback
        self.pos = pos
        self.margin = 20
        self.size = (25,25)

        self.gravity_toggle_off = Rectangle(
            pos=self.pos,
            size=self.size,
            texture=Image('ui/buttons/unchecked.png').texture
        )
        self.gravity_toggle_on = Rectangle(
            pos=self.pos,
            size=(25,25),
            texture=Image('ui/buttons/checked.png').texture
        )
        self.add(self.gravity_toggle_off)

    def in_bounds(self, mouse_pos, obj_pos, obj_size):
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

    def on_touch_down(self, pos):
        button_size = (self.gravity_toggle_off.size[0], self.gravity_toggle_off.size[1])

        if self.in_bounds(pos, self.gravity_toggle_off.pos, button_size):
            self.toggle()

    def toggle(self):
        if self.gravity_toggle_on not in self.children:
            self.add(self.gravity_toggle_on)
            self.callback(True)
        else:
            self.remove(self.gravity_toggle_on)
            self.callback(False)

class TimbreSelect(InstructionGroup):
    """
    Submodule to select the timbre of PhysicsBubble.
    """
    def __init__(self, pos, callback):
        super(TimbreSelect, self).__init__()

        self.selected = 'sine' # the actual important variable: which timbre is selected!

        # callback is needed to update PhysicsBubbleHandler's state for timbre
        self.callback = callback

        self.pos = pos
        self.margin = 20
        self.button_length = 64
        self.title_height = 50 # height of the word 'timbre'
        self.size = (
            (4 * self.button_length) + (5 * self.margin),
            self.button_length + (2 * self.margin) + self.title_height
        )

        self.white = (239/255, 226/255, 222/255)
        self.red = (201/255, 108/255, 130/255)

        self.border_color = Color(1, 0, 0)
        self.border = Line(rectangle=(*self.pos, *self.size))
        self.add(self.border_color)
        self.add(self.border)

        button_size = (self.button_length, self.button_length)
        self.timbres = {
            'sine': Rectangle(size=button_size, texture=Image('images/sine.png').texture),
            'square': Rectangle(size=button_size, texture=Image('images/square.png').texture),
            'triangle': Rectangle(size=button_size, texture=Image('images/triangle.png').texture),
            'sawtooth': Rectangle(size=button_size, texture=Image('images/sawtooth.png').texture)
        }
        self.timbre_bgs = {
            'sine': Rectangle(size=button_size),
            'square': Rectangle(size=button_size),
            'triangle': Rectangle(size=button_size),
            'sawtooth': Rectangle(size=button_size)
        }
        self.timbre_colors = {
            'sine': Color(*self.red), # default selected timbre
            'square': Color(*self.white),
            'triangle': Color(*self.white),
            'sawtooth': Color(*self.white)
        }

        x, y = self.pos

        sine_pos = (x + self.margin, y + self.margin)
        square_pos = (x + 2*self.margin + self.button_length, y + self.margin)
        triangle_pos = (x + 3*self.margin + 2*self.button_length, y + self.margin)
        sawtooth_pos = (x + 4*self.margin + 3*self.button_length, y + self.margin)

        for timbre, timbre_pos in zip(
            ('sine', 'square', 'triangle', 'sawtooth'),
            (sine_pos, square_pos, triangle_pos, sawtooth_pos)
        ):
            self.timbres[timbre].pos = self.timbre_bgs[timbre].pos = timbre_pos
            self.add(self.timbre_colors[timbre])
            self.add(self.timbre_bgs[timbre])
            self.add(self.timbres[timbre])

        title_pos = (x + self.size[0]/2, y + self.size[1] - self.title_height/2 - self.margin/2)
        self.title = CLabelRect(cpos=title_pos, text='timbre', font_size='18')
        self.add(Color(*self.white))
        self.add(self.title)

    def in_bounds(self, mouse_pos, obj_pos, obj_size):
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

    def on_touch_down(self, pos):
        button_size = (self.button_length, self.button_length)

        if self.in_bounds(pos, self.timbres['sine'].pos, button_size):
            self.select('sine')
            self.callback(self.selected)

        if self.in_bounds(pos, self.timbres['square'].pos, button_size):
            self.select('square')
            self.callback(self.selected)

        if self.in_bounds(pos, self.timbres['triangle'].pos, button_size):
            self.select('triangle')
            self.callback(self.selected)

        if self.in_bounds(pos, self.timbres['sawtooth'].pos, button_size):
            self.select('sawtooth')
            self.callback(self.selected)

    def select(self, timbre):
        self.timbre_colors[timbre].rgb = self.red
        self.selected = timbre
        others = [c for c in ['sine', 'square', 'triangle', 'sawtooth'] if c != timbre]
        for o in others:
            self.timbre_colors[o].rgb = self.white
