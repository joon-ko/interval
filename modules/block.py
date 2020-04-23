import sys, os
sys.path.insert(0, os.path.abspath('..'))

from common.core import lookup
from common.gfxutil import topleft_label, CEllipse, CRectangle, CLabelRect, AnimGroup, KFAnim
from common.note import NoteGenerator, Envelope
from kivy.graphics import Color, Line, Rectangle
from kivy.graphics.instructions import InstructionGroup
from kivy.core.image import Image
from kivy.core.window import Window
from kivy.clock import Clock as kivyClock

import numpy as np

from modules.block_gui import BlockGUI

class SoundBlock(InstructionGroup):
    """
    This module is a rectangular, static block that plays a sound when either someone clicks it,
    or another sound module (e.g. PhysicsBubble) collides with it.
    """
    name = 'SoundBlock'

    def __init__(self, sandbox, pos, size, flash, callback=None):
        super(SoundBlock, self).__init__()
        self.sandbox = sandbox
        self.pos = np.array(pos, dtype=np.float)
        self.size = np.array(size, dtype=np.float)
        self.flash = flash
        self.callback = callback

        self.rect = Rectangle(
            pos=self.pos,
            size=self.size,
        )
        self.color = Color(239/255, 226/255, 222/255)
        self.add(self.color)
        self.add(self.rect)

        self.time = 0

        self.on_update(0)

    def on_update(self, dt):
        pass

class SoundBlockHandler(object):
    """
    Handles user interaction and drawing of graphics before generating a SoundBlock.
    Also stores and updates all currently active SoundBlocks.
    """
    def __init__(self, sandbox, mixer, client, client_id):
        self.module_name = 'SoundBlock'
        self.sandbox = sandbox
        self.mixer = mixer
        self.client = client
        self.cid = client_id

        # many variables here are dicts because a user's module handler needs to keep track of
        # not just its own variables, but other users' variables as well! so we use dictionaries
        # with client ids as the keys.
        self.hold_point = {}
        self.hold_shape = {}

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

        self.gui = BlockGUI(pos=(20, 300)) # placeholder

    def on_touch_down(self, cid, pos):
        if not self.sandbox.in_bounds(pos):
            return

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

        bottom_left = self.hold_shape[cid].pos
        size = self.hold_shape[cid].size

        self.sandbox.remove(self.hold_shape[cid])

        block = SoundBlock(self.sandbox, bottom_left, size, False, self.sound)
        self.blocks.add(block)

    def on_key_down(self, cid, key):
        pass

    def display_controls(self):
        return 'this module\'s info coming soon!'

    def on_update(self):
        self.blocks.on_update()

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
        note = NoteGenerator(pitch, 1, timbre)
        env = Envelope(note, 0.01, 1, 0.2, 2)
        self.mixer.add(env)

    def calculate_size(self, corner, pos):
        x = abs(pos[0]-corner[0])
        y = abs(pos[1]-corner[1])
        return (x,y)

    def calculate_center(self, corner, size):
        c_x = corner[0]+(size[0]/2)
        c_y = corner[1]+(size[1]/2)
        return (c_x, c_y)
