import sys, os
sys.path.insert(0, os.path.abspath('..'))

from common.gfxutil import CLabelRect, CRectangle
from kivy.graphics import Color, Line, Rectangle
from kivy.graphics.instructions import InstructionGroup
from kivy.core.image import Image
from kivy.core.window import Window

def midi_pitch_to_note_name(pitch):
    """
    Given a numerical MIDI pitch, return the note name, e.g. "C4".
    Assumes that 24 <= pitch <= 96 (C1 through C7).
    """
    residue_to_note_name = [
        'C',
        'C#/Db',
        'D',
        'D#/Eb',
        'E',
        'F',
        'F#/Gb',
        'G',
        'G#/Ab',
        'A',
        'A#/Bb',
        'B'
    ]
    octave = 1
    residue = pitch - 24
    while (residue - 12 >= 0):
        residue -= 12
        octave += 1
    return '{}{}'.format(residue_to_note_name[residue], octave)

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

class BubbleGUI(InstructionGroup):
    """
    Main interface that controls the GUI for PhysicsBubble.
    """
    def __init__(
        self, norm, pos,
        pitch_callback=None,
        bounce_callback=None,
        gravity_callback=None,
        timbre_callback=None
    ):
        super(BubbleGUI, self).__init__()
        self.norm = norm

        self.pos = pos
        self.size = self.norm.nt((495, 730))

        self.border_color = Color(238/255, 142/255, 154/255) # peach
        self.border = Line(rectangle=(*self.pos, *self.size), width=2)
        self.add(self.border_color)
        self.add(self.border)

        ps_pos = self.norm.nt((self.pos[0]+20, self.pos[1]+20))
        bs_pos = self.norm.nt((self.pos[0]+20, self.pos[1]+300))
        gs_pos = self.norm.nt((self.pos[0]+20, self.pos[1]+450))
        ts_pos = self.norm.nt((self.pos[0]+20, self.pos[1]+560))

        self.ps = PitchSelect(norm, pos=ps_pos, callback=pitch_callback)
        self.bs = BounceSelect(norm, pos=bs_pos, callback=bounce_callback)
        self.gs = GravitySelect(norm, pos=gs_pos, callback=gravity_callback)
        self.ts = TimbreSelect(norm, pos=ts_pos, callback=timbre_callback)

        self.add(self.ps)
        self.add(self.bs)
        self.add(self.gs)
        self.add(self.ts)

    def on_touch_down(self, pos):
        for submodule in [self.ps, self.ts, self.gs, self.bs]:
            if in_bounds(pos, submodule.pos, submodule.size):
                submodule.on_touch_down(pos)

    def on_update(self, pos):
        self.ps.on_update(pos)
        self.bs.on_update(pos)

class PitchSelect(InstructionGroup):
    """
    Submodule to select the pitch of PhysicsBubble in the form of a graphical piano.
    """
    def __init__(self, norm, pos, callback):
        super(PitchSelect, self).__init__()
        self.norm = norm

        self.selected_key = 0
        self.root_pitch = 60
        self.pitch = 60 # default pitch

        self.green = (144/255, 238/255, 144/255)
        self.white = (239/255, 226/255, 222/255)
        self.black = (.2, .2, .2)
        self.color_names = [
            'red', 'orange', 'yellow', 'green', 'teal', 'blue', 'indigo', 'violet',
            'red', 'orange', 'yellow', 'green', 'teal'
        ]
        self.callback = callback
        self.pos = pos
        self.margin = 20
        self.white_key_size = (50, 150)
        self.black_key_size = (40, 100)
        self.key_margin = 2 # pixels of space between keys
        self.size = (
            8*self.white_key_size[0] + 7*self.key_margin + 2*self.margin,
            self.white_key_size[1] + 2*self.margin + 60
        )
        self.border_color = Color(238/255, 234/255, 202/255) # yellow
        self.border = Line(rectangle=(*self.pos, *self.size), width=2)
        self.add(self.border_color)
        self.add(self.border)

        self.keys = [None] * 13
        self.white_keys = [0, 2, 4, 5, 7, 9, 11, 12]
        self.black_keys = [1, 3, 6, 8, 10]
        key_start = (self.pos[0] + self.margin, self.pos[1] + self.margin)
        unit = self.white_key_size[0] + self.key_margin
        black_key_units = [1, 2, 4, 5, 6]
        for i, m in zip(self.white_keys, range(8)):
            self.keys[i] = Rectangle(
                size=self.white_key_size,
                pos=(key_start[0] + m*unit, key_start[1])
            )
        for i, m in zip(self.black_keys, black_key_units):
            self.keys[i] = CRectangle(
                csize=self.black_key_size,
                cpos=(key_start[0] + m*unit, key_start[1] + 100)
            )

        self.key_colors = [None] * 13
        for i in self.white_keys:
            self.key_colors[i] = Color(*self.white)
            self.add(self.key_colors[i])
            self.add(self.keys[i])
        for i in self.black_keys:
            self.key_colors[i] = Color(*self.black)
            self.add(self.key_colors[i])
            self.add(self.keys[i])
        self.key_colors[0].rgb = self.green

        self.arrow_size = (50, 50)
        self.left_pos = (
            self.pos[0] + self.margin,
            self.pos[1] + self.size[1] - self.arrow_size[1] - 10
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
            self.pos[1] + self.size[1] - self.arrow_size[1] - 10
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

        title_pos = (
            self.pos[0] + self.size[0]/2,
            self.pos[1] + self.size[1] - self.margin - 20
        )
        self.title = CLabelRect(
            cpos=title_pos,
            text='pitch: {}'.format(midi_pitch_to_note_name(self.pitch)),
            font_size='18')
        self.add(Color(1, 1, 1))
        self.add(self.title)

    def on_touch_down(self, pos):
        for i in self.black_keys:
            if in_bounds(pos, self.keys[i].pos, self.black_key_size):
                self.select(i)
                return # don't also check for white keys
        for i in self.white_keys:
            if in_bounds(pos, self.keys[i].pos, self.white_key_size):
                self.select(i)

        if in_bounds(pos, self.left_off.pos, self.arrow_size):
            self.left_press()
        if in_bounds(pos, self.right_off.pos, self.arrow_size):
            self.right_press()

    def left_press(self):
        if self.root_pitch - 12 < 24: # don't go below C1 in pitch
            return

        index = self.pitch - self.root_pitch
        self.root_pitch -= 12
        self.pitch -= 12
        self.title.set_text('pitch: {}'.format(midi_pitch_to_note_name(self.pitch)))
        self.callback(self.color_names[index], self.pitch)

    def right_press(self):
        if self.root_pitch + 12 >= 96: # don't go above C7 in pitch
            return

        index = self.pitch - self.root_pitch
        self.root_pitch += 12
        self.pitch += 12
        self.title.set_text('pitch: {}'.format(midi_pitch_to_note_name(self.pitch)))
        self.callback(self.color_names[index], self.pitch)

    def left_anim(self, pos):
        if in_bounds(pos, self.left_off.pos, self.arrow_size):
            if self.left_on not in self.children:
                self.add(self.left_on)
        else:
            if self.left_on in self.children:
                self.remove(self.left_on)

    def right_anim(self, pos):
        if in_bounds(pos, self.right_off.pos, self.arrow_size):
            if self.right_on not in self.children:
                self.add(self.right_on)
        else:
            if self.right_on in self.children:
                self.remove(self.right_on)

    def select(self, key):
        if key == self.selected_key:
            return
        previous_select = self.selected_key
        self.key_colors[key].rgb = self.green
        color = self.white if previous_select in self.white_keys else self.black
        self.key_colors[previous_select].rgb = color
        pitch = self.root_pitch + key
        self.title.set_text('pitch: {}'.format(midi_pitch_to_note_name(pitch)))
        self.pitch = pitch
        self.selected_key = key
        self.callback(self.color_names[key], self.pitch)

    def on_update(self, pos):
        self.left_anim(pos)
        self.right_anim(pos)

class BounceSelect(InstructionGroup):
    """
    Submodule to toggle bounces of PhysicsBubble.
    """
    def __init__(self, norm, pos, callback):
        super(BounceSelect, self).__init__()
        self.norm = norm

        self.bounces = 5

        self.callback = callback
        self.pos = pos
        self.margin = 20
        self.size = (210, 130)

        self.border_color = Color(170/255, 220/255, 206/255) # green
        self.border = Line(rectangle=(*self.pos, *self.size), width=2)
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

    def on_touch_down(self, pos):
        if in_bounds(pos, self.left_off.pos, self.arrow_size):
            self.left_press()
        elif in_bounds(pos, self.right_off.pos, self.arrow_size):
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
        if in_bounds(pos, self.left_off.pos, self.arrow_size):
            if self.left_on not in self.children:
                self.add(self.left_on)
        else:
            if self.left_on in self.children:
                self.remove(self.left_on)

    def right_anim(self, pos):
        if in_bounds(pos, self.right_off.pos, self.arrow_size):
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
    def __init__(self, norm, pos, callback):
        super(GravitySelect, self).__init__()
        self.norm = norm

        self.callback = callback
        self.pos = pos
        self.margin = 20
        self.check_size = (50, 50)
        self.size = (
            210,
            2*self.margin + self.check_size[1]
        )

        self.border_color = Color(50/255, 147/255, 140/255) # bluegreen
        self.border = Line(rectangle=(*self.pos, *self.size), width=2)
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

    def on_touch_down(self, pos):
        button_size = (self.off.size[0], self.off.size[1])
        if in_bounds(pos, self.off.pos, button_size):
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
    def __init__(self, norm, pos, callback):
        super(TimbreSelect, self).__init__()
        self.norm = norm

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

        self.border_color = Color(147/255, 127/255, 159/255) # purple
        self.border = Line(rectangle=(*self.pos, *self.size), width=2)
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

    def on_touch_down(self, pos):
        button_size = (self.button_length, self.button_length)

        if in_bounds(pos, self.timbres['sine'].pos, button_size):
            self.select('sine')
            self.callback(self.selected)

        if in_bounds(pos, self.timbres['square'].pos, button_size):
            self.select('square')
            self.callback(self.selected)

        if in_bounds(pos, self.timbres['triangle'].pos, button_size):
            self.select('triangle')
            self.callback(self.selected)

        if in_bounds(pos, self.timbres['sawtooth'].pos, button_size):
            self.select('sawtooth')
            self.callback(self.selected)

    def select(self, timbre):
        self.timbre_colors[timbre].rgb = self.red
        self.selected = timbre
        others = [c for c in ['sine', 'square', 'triangle', 'sawtooth'] if c != timbre]
        for o in others:
            self.timbre_colors[o].rgb = self.white
