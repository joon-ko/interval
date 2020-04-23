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

from modules.bubble_gui import TimbreSelect, GravitySelect, BounceSelect, PitchSelect
from modules.bubble_gui import BubbleGUI

def timbre_to_shape(timbre, pos):
    if timbre == 'sine':
        return CEllipse(cpos=pos, size=(80, 80), segments=20)
    elif timbre == 'triangle':
        return CEllipse(cpos=pos, size=(90, 90), segments=3)
    elif timbre == 'square':
        return CRectangle(cpos=pos, size=(80, 80))
    elif timbre == 'sawtooth':
        # square rotated 45 degrees
        return CEllipse(cpos=pos, size=(90, 90), segments=4)

downwards_gravity = np.array((0, -1800))
damping_factor = 0.85

class PhysicsBubble(InstructionGroup):
    """
    This module is a drag-and-release physics-based bubble that plays a sound upon colliding with
    another collidable object, including the sandbox edges.
    """
    name = 'PhysicsBubble'

    def __init__(
        self, sandbox, pos, vel, pitch, timbre, color, bounces, gravity=False, callback=None
    ):
        """
        :param sandbox: client's sandbox
        :param pos: initial position
        :param vel: initial velocity
        :param pitch: MIDI pitch value, where 60 is middle C
        :param timbre: type of waveform, e.g. 'sine' or 'sawtooth'
        :param color: 3-tuple of RGB color
        :param bounces: number of times the bubble bounces before fading away
        :param gravity: whether or not the bubble is subjected to downwards gravity
        :param callback: the sound function that is called when the bubble bounces
        """
        super(PhysicsBubble, self).__init__()

        self.sandbox = sandbox

        self.r = 40
        self.pos = np.array(pos, dtype=np.float)
        self.vel = 2 * np.array(vel, dtype=np.float)

        self.pitch = pitch
        self.timbre = timbre
        self.color = Color(*color)
        self.text_color = Color(0, 0, 0)
        self.bounces = bounces
        self.gravity = gravity
        self.callback = callback

        self.text = CLabelRect(cpos=pos, text=str(self.bounces))
        self.bubble = timbre_to_shape(self.timbre, pos)

        self.add(self.color)
        self.add(self.bubble)
        self.add(self.text_color)
        self.add(self.text)

        # have the bubble fade away when self.bounces = 0
        self.fade_anim = KFAnim((0, 1), (0.25, 0))
        self.time = 0

        self.on_update(0)

    def on_update(self, dt):
        if self.gravity:
            self.vel += downwards_gravity * dt
            self.pos += self.vel * dt
        else:
            self.pos += self.vel * dt

        if self.bounces > 0:
            if self.check_for_collisions() and self.callback is not None:
                self.callback(self.pitch, self.timbre)
        # second condition checks if bubble hasn't been moving but there's no gravity --
        # since bubble would be on the screen forever without making sound, fade it away
        if self.bounces <= 0 or (not self.gravity and np.linalg.norm(self.vel) == 0):
            self.color.a = self.fade_anim.eval(self.time)
            self.time += dt

        self.bubble.set_cpos(self.pos)
        self.text.set_cpos(self.pos)

        return self.fade_anim.is_active(self.time)

    def check_for_collisions(self):
        bottom = self.sandbox.pos[1]
        top = self.sandbox.pos[1] + self.sandbox.height
        left = self.sandbox.pos[0]
        right = self.sandbox.pos[0] + self.sandbox.width

        # collision with bottom
        if self.pos[1] - self.r < bottom:
            self.vel[1] = -self.vel[1] * damping_factor if self.gravity else -self.vel[1]
            self.pos[1] = bottom + self.r
            self.bounces -= 1
            self.text.set_text(str(self.bounces))
            return True

        # collision with top
        if self.pos[1] + self.r > top:
            self.vel[1] = -self.vel[1]
            self.pos[1] = top - self.r
            self.bounces -= 1
            self.text.set_text(str(self.bounces))
            return True

        # collision with left
        if self.pos[0] - self.r < left:
            self.vel[0] = -self.vel[0]
            self.pos[0] = left + self.r
            self.bounces -= 1
            self.text.set_text(str(self.bounces))
            return True

        # collision with right
        if self.pos[0] + self.r > right:
            self.vel[0] = -self.vel[0]
            self.pos[0] = right - self.r
            self.bounces -= 1
            self.text.set_text(str(self.bounces))
            return True

class PhysicsBubbleHandler(object):
    """
    Handles user interaction and drawing of graphics before generating a PhysicsBubble.
    Also stores and updates all currently active PhysicsBubbles.
    """
    def __init__(self, sandbox, mixer, client, client_id, block_handler):
        self.module_name = 'PhysicsBubble'
        self.sandbox = sandbox
        self.mixer = mixer
        self.client = client
        self.cid = client_id
        self.block_handler = block_handler

        # many variables here are dicts because a user's module handler needs to keep track of
        # not just its own variables, but other users' variables as well! so we use dictionaries
        # with client ids as the keys.
        self.hold_line = {}
        self.hold_point = {}
        self.hold_shape = {}
        self.text = {}
        self.text_color = Color(0, 0, 0)

        # this mysterious variable is needed for a race condition in which touch_up events are
        # sometimes registered before touch_down events when the user clicks too fast, causing
        # touch_down and touch_up to occur at roughly the same time. if touch_up happens first,
        # it returns early. when touch_down is called later, it **skips** (hence the name)
        # adding shapes to the sandbox, after which this is toggled to False again. basically,
        # nothing is drawn to the screen, which indirectly prompts the user to try again.
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

        self.default_color = self.color_dict['red']
        self.default_pitch = self.pitch_list[0]
        self.default_timbre = 'sine'
        self.default_bounces = 5

        self.color = {}
        self.pitch = {}
        self.timbre = {}
        self.bounces = {}
        self.gravity = {}

        # flag used to only display controls when this module is synced
        # see on_update() and sync_state()
        self.display = False

        self.bubbles = AnimGroup()
        self.sandbox.add(self.bubbles)

        # GUI elements
        self.gui = BubbleGUI(
            pos=(0, 300),
            pitch_callback=self.update_pitch,
            bounce_callback=self.update_bounces,
            gravity_callback=self.update_gravity,
            timbre_callback=self.update_timbre
        )
        self.sandbox.add(self.gui)

    def on_touch_down(self, cid, pos):
        if cid == self.cid:
            self.gui.on_touch_down(pos)

        if not self.sandbox.in_bounds(pos):
            return

        # start drawing drag line and preview of the PhysicsBubble
        self.hold_point[cid] = pos
        self.hold_shape[cid] = timbre_to_shape(self.timbre[cid], pos)
        self.hold_line[cid] = Line(points=(*pos, *pos), width=3)
        self.text[cid] = CLabelRect(cpos=pos, text=str(self.bounces[cid]))

        if self.skip.get(cid) == True:
            self.skip[cid] = False
            return

        self.sandbox.add(Color(*self.color[cid]))
        self.sandbox.add(self.hold_shape[cid])
        self.sandbox.add(self.hold_line[cid])
        self.sandbox.add(self.text_color)
        self.sandbox.add(self.text[cid])

    def on_touch_move(self, cid, pos):
        if not self.sandbox.in_bounds(pos):
            return

        # update the position of the drag line and preview of the PhysicsBubble
        self.hold_shape[cid].set_cpos(pos)
        self.text[cid].set_cpos(pos)
        self.hold_line[cid].points = (*self.hold_point[cid], *pos)

    def on_touch_up(self, cid, pos):
        if (self.hold_shape.get(cid) not in self.sandbox) or \
           (self.text.get(cid) not in self.sandbox) or \
           (self.hold_line.get(cid) not in self.sandbox):
            # if we were currently drawing a preview shape/line but released the mouse out of
            # bounds, we should release the shape anyway as a QOL measure
            if not self.sandbox.in_bounds(pos):
                return
            else:
                self.skip[cid] = True
                return

        self.sandbox.remove(self.hold_shape[cid])
        self.sandbox.remove(self.text[cid])
        self.sandbox.remove(self.hold_line[cid])

        # calculate velocity
        hold_point = self.hold_point[cid]
        dx = pos[0] - hold_point[0]
        dy = pos[1] - hold_point[1]
        vel = (-dx, -dy)

        pitch = self.pitch[cid]
        timbre = self.timbre[cid]
        color = self.color[cid]
        bounces = self.bounces[cid]
        gravity = self.gravity[cid]

        # release the PhysicsBubble
        bubble = PhysicsBubble(
            self.sandbox, pos, vel, pitch, timbre, color, bounces,
            gravity=gravity, callback=self.sound
        )
        self.bubbles.add(bubble)

    def on_key_down(self, cid, key):
        index = lookup(key, 'q2w3er5t6y7ui', range(13))
        if index is not None:
            if self.cid == cid:
                self.gui.ps.select(index)
        if key == '[':
            if cid == self.cid:
                self.gui.ps.left_press()
        if key == ']':
            if cid == self.cid:
                self.gui.ps.right_press()

        d_bounces = lookup(key, ['right', 'left'], [1, -1])
        if d_bounces is not None:
            self.bounces[cid] += d_bounces
            if cid == self.cid:
                self.gui.bs.update_bounces(self.bounces[cid])

        timbre = lookup(key, 'asdf', ['sine', 'square', 'triangle', 'sawtooth'])
        if timbre is not None:
            self.timbre[cid] = timbre
            if self.cid == cid:
                self.gui.ts.select(timbre) # have the GUI update as well

        if key == 'g': # toggle gravity
            if cid == self.cid:
                self.gravity[cid] = not self.gravity[cid]
                self.gui.gs.toggle()

        # other clients should update their state to reflect this client's new selection.
        if self.cid == cid: # don't want every client updating server's state at the same time!
            self.update_server_state(post=False)

    def sound(self, pitch, timbre):
        """
        Play a sound when a PhysicsBubble collides with a collidable object.
        """
        note = NoteGenerator(pitch, 1, timbre)
        env = Envelope(note, 0.01, 1, 0.2, 2)
        self.mixer.add(env)

    def update_pitch(self, color, pitch):
        """Update this client's color and pitch due to PitchSelect."""

        self.color[self.cid] = self.color_dict[color]
        self.pitch[self.cid] = pitch
        self.update_server_state(post=True)

    def update_timbre(self, timbre):
        """Update this client's timbre due to TimbreSelect."""

        self.timbre[self.cid] = timbre
        self.update_server_state(post=True)

    def update_gravity(self, gravity):
        """Update this client's gravity due to GravitySelect."""

        self.gravity[self.cid] = gravity
        self.update_server_state(post=True)

    def update_bounces(self, bounces):
        """Update this client's bounces due to BounceSelect."""

        self.bounces[self.cid] = bounces
        self.update_server_state(post=True)

    def display_controls(self):
        """Provides additional text info specific to this module to go on the top-left label."""

        return 'click and drag!'

    def on_update(self):
        self.bubbles.on_update()
        self.gui.on_update(Window.mouse_pos)

    def update_server_state(self, post=False):
        """Update server state. If post is True, relay this updated state to all clients."""

        state = {
            'color': self.color,
            'pitch': self.pitch,
            'timbre': self.timbre,
            'bounces': self.bounces,
            'gravity': self.gravity
        }
        data = {'module': self.module_name, 'cid': self.cid, 'state': state, 'post': post}
        self.client.emit('update_state', data)

    def update_client_state(self, cid, state):
        """Update this handler's state."""

        if cid != self.cid: # this client already updated its own state
            self.color = state['color']
            self.pitch = state['pitch']
            self.timbre = state['timbre']
            self.bounces = state['bounces']
            self.gravity = state['gravity']

    def sync_state(self, state):
        """
        Initial sync with the server's copy of module state.
        We don't sync with hold_shape, hold_point, and hold_line because those objects are not
        json-serializable and are short-term values anyway.
        """
        self.color = state['color']
        self.pitch = state['pitch']
        self.timbre = state['timbre']
        self.bounces = state['bounces']
        self.gravity = state['gravity']

        # after initial sync, add default values for this client
        self.color[self.cid] = self.default_color
        self.pitch[self.cid] = self.default_pitch
        self.timbre[self.cid] = self.default_timbre
        self.bounces[self.cid] = self.default_bounces
        self.gravity[self.cid] = False
        self.skip[self.cid] = False

        # now that default values are set, we can display this module's info
        self.display = True

        # update server with these default values
        # post=True here because we want all other clients' states to update with this client's
        # default values.
        self.update_server_state(post=True)
