import sys, os
sys.path.insert(0, os.path.abspath('..'))

from common.core import lookup
from common.gfxutil import topleft_label, CEllipse, CRectangle, CLabelRect, AnimGroup, KFAnim
from common.note import NoteGenerator, Envelope
from common.synth import Synth
from common.audio import Audio

from kivy.graphics import Color, Line, Rectangle
from kivy.graphics.instructions import InstructionGroup
from kivy.core.image import Image
from kivy.core.window import Window
from kivy.clock import Clock as kivyClock
from common.clock import Clock, SimpleTempoMap, Scheduler, AudioScheduler, tick_str, kTicksPerQuarter

import numpy as np

from modules.block_gui import BlockGUI

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

class SoundBlock(InstructionGroup):
    """
    This module is a rectangular, static block that plays a sound when either someone clicks it,
    or another sound module (e.g. PhysicsBubble) collides with it.
    """
    name = 'SoundBlock'

    def __init__(self, norm, sandbox, pos, size, handler, callback=None):
        super(SoundBlock, self).__init__()
        self.norm = norm
        self.sandbox = sandbox
        self.pos = np.array(pos, dtype=np.float)
        self.size = np.array(size, dtype=np.float)
        self.handler = handler
        self.callback = callback

        self.rect = Rectangle(
            pos=self.pos,
            size=self.size,
        )
        self.white = (239/255, 226/255, 222/255)
        self.color = Color(*self.white)
        self.add(self.color)
        self.add(self.rect)

        self.hit = False
        self.hit_color = (201/255, 108/255, 130/255)
        self.flash_anim = KFAnim((0, *self.hit_color), (.25, *self.white))
        self.pitch = 60
        self.clock = Clock()
        self.tempo_map = SimpleTempoMap(120)
        self.sched = Scheduler(self.clock, self.tempo_map)

        self.time = 0

    def flash(self):
        self.callback(self.pitch, 'sine')
        self.time = self.sched.get_time()
        self.hit = True

    def on_update(self, dt):
        if self.hit:
            rgb = self.flash_anim.eval(self.time)
            self.color.rgb = rgb
            self.time += dt
            if not self.flash_anim.is_active(self.time):
                self.hit = False
                self.time = 0

class SoundBlockHandler(object):
    """
    Handles user interaction and drawing of graphics before generating a SoundBlock.
    Also stores and updates all currently active SoundBlocks.
    """
    def __init__(self, norm, sandbox, mixer, client, client_id):
        self.norm = norm
        self.module_name = 'SoundBlock'
        self.sandbox = sandbox
        #self.mixer = mixer
        self.clock = Clock()
        self.tempo_map = SimpleTempoMap(120)
        self.audio = Audio(2)
        self.synth = Synth("data/FluidR3_GM.sf2")
        self.sched = Scheduler(self.clock, self.tempo_map)
        self.audio.set_generator(self.synth)
        self.client = client
        self.cid = client_id

        #set up the correct sound (program: bank and preset)
        self.synth.program(0, 0, 80) #default to piano
        self.playing = False

        # many variables here are dicts because a user's module handler needs to keep track of
        # not just its own variables, but other users' variables as well! so we use dictionaries
        # with client ids as the keys.
        self.hold_point = {}
        self.hold_shape = {}

        # this variable is needed for when a user clicks on a soundblock in a touch_down event,
        # so that the corresponding touch_up event is skipped
        self.skip = {}

        self.color_dict = {
            'red': (201/255, 108/255, 130/255),
            'orange': (214/255, 152/255, 142/255),
            'yellow': (238/255, 234/255, 202/255),
            'green': (170/255, 220/255, 206/255),
            'teal': (159/255, 187/255, 208/255),
            'blue': (44/255, 85/255, 123/255),
            'indigo': (46/255, 40/255, 90/255),
            'violet': (147/255, 127/255, 159/255),
            'white': (239/255, 226/255, 222/255)
        }
        self.pitch_list = [60, 62, 64, 65, 67, 69, 71, 72]

        self.default_color = self.color_dict['violet']
        self.default_pitch = self.pitch_list[0]
        self.default_timbre = 'sine'

        self.color = {}
        self.pitch = {}
        self.timbre = {}

        self.display = False

        self.blocks = AnimGroup()
        self.sandbox.add(self.blocks)

        self.gui = BlockGUI(self.norm, pos=self.norm.nt((20, 300))) # placeholder

    def on_touch_down(self, cid, pos):
        if not self.sandbox.in_bounds(pos):
            return

        # when a block is clicked, flash and play a sound
        for block in self.blocks.objects:
            if in_bounds(pos, block.pos, block.size):
                block.flash()
                self.skip[cid] = True
                return # don't start drawing a SoundBlock

        self.hold_point[cid] = pos
        self.hold_shape[cid] = Rectangle(pos = pos, size = (0,0))

        self.sandbox.add(Color(1, 1, 1))
        self.sandbox.add(self.hold_shape[cid])

    def on_touch_move(self, cid, pos):
        if not self.sandbox.in_bounds(pos):
            return

        #determine which direction rectangle is being created in
        hold_point = self.hold_point[cid]
        size = self.calculate_size(hold_point, pos)
        bottom_left = pos

        #moving northeast
        if pos[0] > hold_point[0] and pos[1] > hold_point[1]:
            bottom_left = hold_point

        #moving southeast
        elif pos[0] > hold_point[0] and pos[1] < hold_point[1]:
            bottom_left = (hold_point[0], pos[1])

        #moving southwest
        elif pos[0] < hold_point[0] and pos[1] < hold_point[1]:
            bottom_left = pos

        #moving northwest
        elif pos[0] < hold_point[0] and pos[1] > hold_point[1]:
            bottom_left = (pos[0], hold_point[1])

        self.hold_shape[cid].pos = bottom_left
        self.hold_shape[cid].size = size

    def on_touch_up(self, cid, pos):
        if not self.sandbox.in_bounds(pos):
            return

        if self.skip[cid]:
            self.skip[cid] = False
            return

        bottom_left = self.hold_shape[cid].pos
        size = self.hold_shape[cid].size

        if size[0] <= 10 or size[1] <= 10:
            self.sandbox.remove(self.hold_shape[cid])
            return

        self.sandbox.remove(self.hold_shape[cid])
        block = SoundBlock(self.norm, self.sandbox, bottom_left, size, self, self.sound)
        self.blocks.add(block)

    def on_key_down(self, cid, key):
        pass

    def display_controls(self):
        return 'this module\'s info coming soon!'

    def on_update(self):
        self.blocks.on_update()
        self.audio.on_update()
        self.sched.on_update()

        for block in self.blocks.objects:
            if self.sched.get_time() > block.time + 1:
                    self.synth.noteoff(0, block.pitch)

    def update_server_state(self, post=False):
        """
        Update server state. If post is True, relay this updated state to all clients.
        """
        state = {
            'color': self.color,
            'pitch': self.pitch,
            'timbre': self.timbre
        }
        data = {'module': self.module_name, 'cid': self.cid, 'state': state, 'post': post}
        self.client.emit('update_state', data)

    def update_client_state(self, cid, state):
        """
        Update this handler's state.
        """
        if cid != self.cid: # this client already updated its own state
            self.color = state['color']
            self.pitch = state['pitch']
            self.timbre = state['timbre']

    def sync_state(self, state):
        """
        Initial sync with the server's copy of module state.
        We don't sync with hold_shape, hold_point, and hold_line because those objects are not
        json-serializable and are short-term values anyway.
        """
        self.color = state['color']
        self.pitch = state['pitch']
        self.timbre = state['timbre']

        # after initial sync, add default values for this client
        self.color[self.cid] = self.default_color
        self.pitch[self.cid] = self.default_pitch
        self.timbre[self.cid] = self.default_timbre
        self.skip[self.cid] = False

        # now that default values are set, we can display this module's info
        self.display = True

        # update server with these default values
        # post=True here because we want all other clients' states to update with this client's
        # default values.
        self.update_server_state(post=True)

    def sound(self, pitch, timbre):
        """
        Play a sound when a PhysicsBubble collides with a collidable object.
        """
        self.synth.noteon(0, pitch, 100)


    def calculate_size(self, corner, pos):
        x = abs(pos[0]-corner[0])
        y = abs(pos[1]-corner[1])
        return (x,y)

    def calculate_center(self, corner, size):
        c_x = corner[0]+(size[0]/2)
        c_y = corner[1]+(size[1]/2)
        return (c_x, c_y)
