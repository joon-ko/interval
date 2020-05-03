import sys, os
sys.path.insert(0, os.path.abspath('..'))

from common.gfxutil import CLabelRect, CRectangle
from kivy.graphics import Color, Line, Rectangle
from kivy.graphics.instructions import InstructionGroup
from kivy.core.image import Image

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

class BlockGUI(InstructionGroup):
    def __init__(self, norm, pos, is_drum, pitch_callback, instrument_callback, drum_callback):
        super(BlockGUI, self).__init__()

        self.norm = norm
        self.pos = pos
        self.is_drum = is_drum
        self.size = self.norm.nt((495, 495))
        self.ds_size = self.norm.nt((495, 200))

        ps_pos = (self.pos[0]+self.norm.nv(20), self.pos[1]+self.norm.nv(20))
        is_pos = (self.pos[0]+self.norm.nv(30), self.pos[1]+self.norm.nv(300))
        ds_pos = (self.pos[0]+self.norm.nv(20), self.pos[1]+self.norm.nv(600))
        self.ps = PitchSelect(norm, ps_pos, pitch_callback)
        self.ints = InstrumentSelect(norm, is_pos, instrument_callback)
        self.ds = DrumSelect(norm, ds_pos, drum_callback)

        self.highlight_color = Color(1,1,1)

        if not is_drum:
            self.highlight = Line(rectangle=(*self.pos, *self.size), width=2)
            self.highlight_pos = self.pos
        else:
            self.highlight = Line(rectangle=(*self.ds.pos, *self.size), width=2)
            self.highlight_pos = self.ds.pos

        self.add(self.highlight_color)
        self.add(self.highlight)
        self.add(self.ps)
        self.add(self.ints)
        self.add(self.ds)

    def on_touch_down(self, pos):
        if self.is_drum and (in_bounds(pos, self.ps.pos, self.ps.size) or in_bounds(pos, self.ints.pos, self.ints.size)):
            return
        elif not self.is_drum and in_bounds(pos, self.ds.pos, self.ds.size):
            return
        for submodule in [self.ps, self.ints, self.ds]:
            if in_bounds(pos, submodule.pos, submodule.size):
                submodule.on_touch_down(pos)

    def switch_module(self):
        self.is_drum = not self.is_drum
        if not self.is_drum:
            self.remove(self.highlight)
            self.highlight_pos = self.pos
            self.highlight = Line(rectangle=(*self.highlight_pos, *self.size), width=2)
            self.add(self.highlight)
            
        else:
            self.remove(self.highlight)
            self.highlight_pos = (self.ds.pos[0]-self.norm.nv(24), self.ds.pos[1]-self.norm.nv(18))
            self.highlight = Line(rectangle=(*self.highlight_pos, *self.ds_size), width=2)
            self.add(self.highlight)
            self.highlight_pos = self.ds.pos

    def on_update(self, pos):
        self.ps.on_update(pos)


class DrumSelect(InstructionGroup):
    """
    Submodule to toggle drum kit for SoundBlock.
    """
    def __init__(self, norm, pos, callback):
        super(DrumSelect, self).__init__()
        self.norm = norm
        self.selected = 'snare'

        self.callback = callback
        self.pos = pos
        self.margin = self.norm.nv(20)
        self.button_length = self.norm.nv(64)
        self.title_height = self.norm.nv(50) # height of the word 'drumset'

        self.size = (
                (5 * self.button_length) + (6 * self.margin),
                self.button_length + (2 * self.margin) + self.title_height
            )

        self.white = (239/255, 226/255, 222/255)
        self.red = (201/255, 108/255, 130/255)

        self.border_color = Color(214/255, 152/255, 142/255) #orange
        self.border = Line(rectangle=(*self.pos, *self.size), width=2)
        self.add(self.border_color)
        self.add(self.border)

        button_size = (self.button_length, self.button_length)
        self.instruments = {
            'snare': Rectangle(size=button_size, texture=Image('images/snare.png').texture),
            'crash': Rectangle(size=button_size, texture=Image('images/crash.png').texture),
            'bass': Rectangle(size=button_size, texture=Image('images/bass.png').texture),
            'hihat': Rectangle(size=button_size, texture=Image('images/hihat.png').texture),
            'triangle': Rectangle(size=button_size, texture=Image('images/triangle_instr.png').texture)
        }
        self.instrument_bgs = {
            'snare': Rectangle(size=button_size),
            'crash': Rectangle(size=button_size),
            'bass': Rectangle(size=button_size),
            'hihat': Rectangle(size=button_size),
            'triangle': Rectangle(size=button_size)
        }
        self.instrument_colors = {
            'snare': Color(*self.red), # default selected timbre
            'crash': Color(*self.white),
            'bass': Color(*self.white),
            'hihat': Color(*self.white),
            'triangle': Color(*self.white)
        }

        x, y = self.pos

        snare_pos = (x + self.margin, y + self.margin)
        crash_pos = (x + 2*self.margin + self.button_length, y + self.margin)
        bass_pos = (x + 3*self.margin + 2*self.button_length, y + self.margin)
        hihat_pos = (x + 4*self.margin + 3*self.button_length, y + self.margin)
        triangle_pos = (x + 5*self.margin + 4*self.button_length, y + self.margin)

        for instrument, instrument_pos in zip(
            ('snare', 'crash', 'bass', 'hihat', 'triangle'),
            (snare_pos, crash_pos, bass_pos, hihat_pos, triangle_pos)
        ):
            self.instruments[instrument].pos = self.instrument_bgs[instrument].pos = instrument_pos
            self.add(self.instrument_colors[instrument])
            self.add(self.instrument_bgs[instrument])
            self.add(self.instruments[instrument])

        title_pos = (x + self.size[0]/2, y + self.size[1] - self.title_height/2 - self.margin/2)
        self.title = CLabelRect(cpos=title_pos, text='drumkit', font_size='18')
        self.add(Color(*self.white))
        self.add(self.title)

    def on_touch_down(self, pos):
        button_size = (self.button_length, self.button_length)

        if in_bounds(pos, self.instruments['snare'].pos, button_size):
            self.select('snare')
            self.callback(self.selected)

        if in_bounds(pos, self.instruments['crash'].pos, button_size):
            self.select('crash')
            self.callback(self.selected)

        if in_bounds(pos, self.instruments['bass'].pos, button_size):
            self.select('bass')
            self.callback(self.selected)

        if in_bounds(pos, self.instruments['hihat'].pos, button_size):
            self.select('hihat')
            self.callback(self.selected)

        if in_bounds(pos, self.instruments['triangle'].pos, button_size):
            self.select('triangle')
            self.callback(self.selected)

    def select(self, instrument):
        self.instrument_colors[instrument].rgb = self.red
        self.selected = instrument
        others = [c for c in ['snare', 'crash', 'bass', 'hihat', 'triangle'] if c != instrument]
        for o in others:
            self.instrument_colors[o].rgb = self.white



class InstrumentSelect(InstructionGroup):
    """
    Submodule to select the instrument of SoundBlock.
    """
    def __init__(self, norm, pos, callback):
        super(InstrumentSelect, self).__init__()
        self.norm = norm
        self.selected = 'piano'

        self.callback = callback
        self.pos = pos
        self.margin = self.norm.nv(20)
        self.button_length = self.norm.nv(64)
        self.title_height = self.norm.nv(50) # height of the word 'instrument'

        self.size = (
            (5 * self.button_length) + (6 * self.margin),
            self.button_length + (2 * self.margin) + self.title_height
        )

        self.white = (239/255, 226/255, 222/255)
        self.red = (201/255, 108/255, 130/255)

        self.border_color = Color(147/255, 127/255, 159/255) # purple
        self.border = Line(rectangle=(*self.pos, *self.size), width=2)
        self.add(self.border_color)
        self.add(self.border)

        button_size = (self.button_length, self.button_length)
        self.instruments = {
            'piano': Rectangle(size=button_size, texture=Image('images/piano.png').texture),
            'violin': Rectangle(size=button_size, texture=Image('images/violin.png').texture),
            'trumpet': Rectangle(size=button_size, texture=Image('images/trumpet.png').texture),
            'ocarina': Rectangle(size=button_size, texture=Image('images/ocarina.png').texture),
            'choir': Rectangle(size=button_size, texture=Image('images/choir.png').texture)
        }
        self.instrument_bgs = {
            'piano': Rectangle(size=button_size),
            'violin': Rectangle(size=button_size),
            'trumpet': Rectangle(size=button_size),
            'ocarina': Rectangle(size=button_size),
            'choir': Rectangle(size=button_size)
        }
        self.instrument_colors = {
            'piano': Color(*self.red), # default selected timbre
            'violin': Color(*self.white),
            'trumpet': Color(*self.white),
            'ocarina': Color(*self.white),
            'choir': Color(*self.white)
        }

        x, y = self.pos

        piano_pos = (x + self.margin, y + self.margin)
        violin_pos = (x + 2*self.margin + self.button_length, y + self.margin)
        trumpet_pos = (x + 3*self.margin + 2*self.button_length, y + self.margin)
        ocarina_pos = (x + 4*self.margin + 3*self.button_length, y + self.margin)
        choir_pos = (x + 5*self.margin + 4*self.button_length, y + self.margin)

        for instrument, instrument_pos in zip(
            ('piano', 'violin', 'trumpet', 'ocarina', 'choir'),
            (piano_pos, violin_pos, trumpet_pos, ocarina_pos, choir_pos)
        ):
            self.instruments[instrument].pos = self.instrument_bgs[instrument].pos = instrument_pos
            self.add(self.instrument_colors[instrument])
            self.add(self.instrument_bgs[instrument])
            self.add(self.instruments[instrument])

        title_pos = (x + self.size[0]/2, y + self.size[1] - self.title_height/2 - self.margin/2)
        self.title = CLabelRect(cpos=title_pos, text='instrument', font_size='18')
        self.add(Color(*self.white))
        self.add(self.title)

    def on_touch_down(self, pos):
        button_size = (self.button_length, self.button_length)

        if in_bounds(pos, self.instruments['piano'].pos, button_size):
            self.select('piano')
            self.callback(self.selected)

        if in_bounds(pos, self.instruments['violin'].pos, button_size):
            self.select('violin')
            self.callback(self.selected)

        if in_bounds(pos, self.instruments['trumpet'].pos, button_size):
            self.select('trumpet')
            self.callback(self.selected)

        if in_bounds(pos, self.instruments['ocarina'].pos, button_size):
            self.select('ocarina')
            self.callback(self.selected)

        if in_bounds(pos, self.instruments['choir'].pos, button_size):
            self.select('choir')
            self.callback(self.selected)

    def select(self, instrument):
        self.instrument_colors[instrument].rgb = self.red
        self.selected = instrument
        others = [c for c in ['piano', 'violin', 'trumpet', 'ocarina', 'choir'] if c != instrument]
        for o in others:
            self.instrument_colors[o].rgb = self.white


class PitchSelect(InstructionGroup):
    """
    Submodule to select the instrument pitch of SoundBlock in the form of a graphical piano.
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
            'turquoise', 'pink', 'peach', 'magenta', 'grey'
        ]
        self.callback = callback
        self.pos = pos
        self.margin = self.norm.nv(20)
        self.white_key_size = self.norm.nt((50, 150))
        self.black_key_size = self.norm.nt((40, 100))
        self.key_margin = self.norm.nv(2) # pixels of space between keys
        self.size = (
            8*self.white_key_size[0] + 7*self.key_margin + 2*self.margin,
            self.white_key_size[1] + 2*self.margin + self.norm.nv(60)
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
                cpos=(key_start[0] + m*unit, key_start[1] + self.norm.nv(100))
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

        self.arrow_size = self.norm.nt((50, 50))
        self.left_pos = (
            self.pos[0] + self.margin,
            self.pos[1] + self.size[1] - self.arrow_size[1] - self.norm.nv(10)
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
            self.pos[1] + self.size[1] - self.arrow_size[1] - self.norm.nv(10)
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
            self.pos[1] + self.size[1] - self.margin - self.norm.nv(20)
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
