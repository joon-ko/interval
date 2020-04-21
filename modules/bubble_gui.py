import sys, os
sys.path.insert(0, os.path.abspath('..'))

from common.gfxutil import CLabelRect
from kivy.graphics import Color, Line, Rectangle
from kivy.graphics.instructions import InstructionGroup
from kivy.core.image import Image

class PitchSelect(InstructionGroup):
    """
    Submodule to select the pitch of PhysicsBubble in the form of a graphical piano.
    """
    def __init__(self, pos, callback):
        super(PitchSelect, self).__init__()

        self.selected_key = 0
        self.pitch = 60 # default pitch

        self.green = (144/255, 238/255, 144/255)
        self.white = (239/255, 226/255, 222/255)
        self.midi_to_note_name = {
            60: 'C4',
            62: 'D4',
            64: 'E4',
            65: 'F4',
            67: 'G4',
            69: 'A4',
            71: 'B4',
            72: 'C4'
        }

        self.callback = callback
        self.pos = pos
        self.margin = 20
        self.key_size = (50, 150)
        self.key_margin = 2 # pixels of space between keys
        self.size = (
            8*self.key_size[0] + 7*self.key_margin + 2*self.margin,
            self.key_size[1] + 2*self.margin + 40
        )

        self.border_color = Color(1, 0, 0)
        self.border = Line(rectangle=(*self.pos, *self.size))
        self.add(self.border_color)
        self.add(self.border)

        start_pos = (self.pos[0] + self.margin, self.pos[1] + self.margin)
        unit = self.key_size[0] + self.key_margin
        self.keys = [
            Rectangle(
                size=self.key_size,
                pos=(start_pos[0] + m*unit, start_pos[1])
            )
            for m in range(8)
        ]
        self.key_colors = [Color(*self.white) for c in range(8)]
        self.key_colors[0].rgb = self.green
        for i in range(8):
            self.add(self.key_colors[i])
            self.add(self.keys[i])

        title_pos = (
            self.size[0]/2,
            self.pos[1] + self.size[1] - self.margin - 10
        )
        self.title = CLabelRect(
            cpos=title_pos,
            text='pitch: {}'.format(self.midi_to_note_name[self.pitch]),
            font_size='18')
        self.add(Color(1, 1, 1))
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
        pitches = [60, 62, 64, 65, 67, 69, 71, 72]
        color_names = ['red', 'orange', 'yellow', 'green', 'teal', 'blue', 'indigo', 'violet']
        for i in range(8):
            if self.in_bounds(pos, self.keys[i].pos, self.key_size):
                self.select(i)
                self.callback(color_names[i], pitches[i])

    def select(self, key):
        if key == self.selected_key:
            return
        pitches = [60, 62, 64, 65, 67, 69, 71, 72]
        previous_select = self.selected_key
        self.key_colors[key].rgb = self.green
        self.key_colors[previous_select].rgb = self.white
        self.title.set_text('pitch: {}'.format(self.midi_to_note_name[pitches[key]]))
        self.pitch = pitches[key]
        self.selected_key = key

class BounceSelect(InstructionGroup):
    """
    Submodule to toggle bounces of PhysicsBubble.
    """
    def __init__(self, default_bounces, pos, callback):
        super(BounceSelect, self).__init__()

        self.bounces = default_bounces

        self.callback = callback
        self.pos = pos
        self.margin = 20
        self.size = (210, 130)

        self.border_color = Color(1, 0, 0)
        self.border = Line(rectangle=(*self.pos, *self.size))
        self.add(self.border_color)
        self.add(self.border)

        self.arrow_size = (50, 50)
        self.left_pos = (
            self.pos[0] + self.margin,
            self.pos[1] + self.margin
        )
        self.left_off = Rectangle(
            pos=self.left_pos,
            size=self.arrow_size,
            texture=Image('ui/buttons/left_arrow.png').texture
        )
        self.left_on = Rectangle(
            pos=self.left_pos,
            size=self.arrow_size,
            texture=Image('ui/buttons/left_arrow_clicked.png').texture
        )
        self.right_pos = (
            self.pos[0] + self.size[0] - self.margin - self.arrow_size[0],
            self.pos[1] + self.margin
        )
        self.right_off = Rectangle(
            pos=self.right_pos,
            size=self.arrow_size,
            texture=Image('ui/buttons/right_arrow.png').texture
        )
        self.right_on = Rectangle(
            pos=self.right_pos,
            size=self.arrow_size,
            texture=Image('ui/buttons/right_arrow_clicked.png').texture
        )
        # left_off and right_off are always drawn, but when user mouses over an arrow,
        # left_on and right_on are drawn over left_off and right_off
        self.add(Color(1, 1, 1))
        self.add(self.left_off)
        self.add(self.right_off)

        title_pos = (self.pos[0] + self.size[0]/2, self.pos[1] + self.size[1] - 30)
        self.title = CLabelRect(cpos=title_pos, text='bounces', font_size='18')
        self.add(self.title)

        bounce_text_pos = (
            self.pos[0] + self.size[0]/2,
            self.pos[1] + self.margin + self.arrow_size[1]/2
        )
        self.bounce_text = CLabelRect(cpos=bounce_text_pos, text=str(self.bounces), font_size='18')
        self.add(self.bounce_text)

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
        if self.in_bounds(pos, self.left_off.pos, self.arrow_size):
            self.left_press()
        elif self.in_bounds(pos, self.right_off.pos, self.arrow_size):
            self.right_press()

    def left_press(self):
        self.bounces -= 1
        self.bounce_text.set_text(str(self.bounces))
        self.callback(self.bounces)

    def right_press(self):
        self.bounces += 1
        self.bounce_text.set_text(str(self.bounces))
        self.callback(self.bounces)

    def left_anim(self, pos):
        if self.in_bounds(pos, self.left_off.pos, self.arrow_size):
            if self.left_on not in self.children:
                self.add(self.left_on)
        else:
            if self.left_on in self.children:
                self.remove(self.left_on)

    def right_anim(self, pos):
        if self.in_bounds(pos, self.right_off.pos, self.arrow_size):
            if self.right_on not in self.children:
                self.add(self.right_on)
        else:
            if self.right_on in self.children:
                self.remove(self.right_on)

    def update_bounces(self, bounces):
        self.bounces = bounces
        self.bounce_text.set_text(str(bounces))

    def on_update(self, pos):
        self.left_anim(pos)
        self.right_anim(pos)


class GravitySelect(InstructionGroup):
    """
    Submodule to toggle gravity of PhysicsBubble.
    """
    def __init__(self, pos, callback):
        super(GravitySelect, self).__init__()

        self.callback = callback
        self.pos = pos
        self.margin = 20
        self.check_size = (50, 50)
        self.size = (
            210,
            2*self.margin + self.check_size[1]
        )

        self.border_color = Color(1, 0, 0)
        self.border = Line(rectangle=(*self.pos, *self.size))
        self.add(self.border_color)
        self.add(self.border)

        self.check_color = Color(1, 1, 1)
        self.off = Rectangle(
            pos=(self.pos[0] + self.margin, self.pos[1] + self.margin),
            size=self.check_size,
            texture=Image('ui/buttons/unchecked.png').texture
        )
        self.on = Rectangle(
            pos=(self.pos[0] + self.margin, self.pos[1] + self.margin),
            size=self.check_size,
            texture=Image('ui/buttons/checked.png').texture
        )
        self.add(self.check_color)
        self.add(self.off)

        title_pos = (self.pos[0] + 140, self.pos[1] + self.check_size[1]/2 + self.margin)
        self.title = CLabelRect(cpos=title_pos, text='gravity', font_size='18')
        self.add(Color(1, 1, 1))
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
        button_size = (self.off.size[0], self.off.size[1])
        if self.in_bounds(pos, self.off.pos, button_size):
            self.toggle()

    def toggle(self):
        if self.on not in self.children:
            self.add(self.on)
            self.callback(True)
        else:
            self.remove(self.on)
            self.callback(False)

class TimbreSelect(InstructionGroup):
    """
    Submodule to select the timbre of PhysicsBubble.
    """
    def __init__(self, pos, callback):
        super(TimbreSelect, self).__init__()

        self.selected = 'sine' # the actual important variable: which timbre is selected!

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
