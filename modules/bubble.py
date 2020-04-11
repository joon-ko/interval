import sys, os
sys.path.insert(0, os.path.abspath('..'))

from common.core import lookup
from common.gfxutil import topleft_label, CEllipse, CLabelRect, AnimGroup
from common.note import NoteGenerator, Envelope
from kivy.graphics import Color, Line
from kivy.graphics.instructions import InstructionGroup
from kivy.core.window import Window

import numpy as np

class PhysicsBubble(InstructionGroup):
    """
    This module is a drag-and-release physics-based bubble that plays a sound upon colliding with
    another collidable object, including the sandbox edges.
    """
    name = 'PhysicsBubble'

    def __init__(self, pos, vel, pitch, color, callback=None):
        super(PhysicsBubble, self).__init__()

        self.r = 40
        self.pos = np.array(pos, dtype=np.float)
        self.vel = 2 * np.array(vel, dtype=np.float)

        self.bounces = 5 # hard-code a value for now
        self.pitch = pitch
        self.color = Color(*color)
        self.text_color = Color(0, 0, 0)

        self.text = CLabelRect(cpos=pos, text=str(self.bounces))
        self.bubble = CEllipse(cpos=pos, csize=(80, 80))

        self.add(self.color)
        self.add(self.bubble)
        self.add(self.text_color)
        self.add(self.text)

        self.callback = callback
        self.on_update(0)

    def on_update(self, dt):
        self.pos += self.vel * dt

        if self.bounces != 0:
            if self.check_for_collisions() and self.callback is not None:
                self.callback(self.pitch)

        self.bubble.set_cpos(self.pos)
        self.text.set_cpos(self.pos)

        return True

    def check_for_collisions(self):
        # collision with bottom
        if self.pos[1] - self.r < 0:
            self.vel[1] = -self.vel[1]
            self.pos[1] = self.r
            self.bounces -= 1
            self.text.set_text(str(self.bounces))
            return True

        # collision with top
        if self.pos[1] + self.r > Window.height:
            self.vel[1] = -self.vel[1]
            self.pos[1] = Window.height - self.r
            self.bounces -= 1
            self.text.set_text(str(self.bounces))
            return True

        # collision with left
        if self.pos[0] - self.r < 0:
            self.vel[0] = -self.vel[0]
            self.pos[0] = self.r
            self.bounces -= 1
            self.text.set_text(str(self.bounces))
            return True

        # collision with right
        if self.pos[0] + self.r > Window.width:
            self.vel[0] = -self.vel[0]
            self.pos[0] = Window.width - self.r
            self.bounces -= 1
            self.text.set_text(str(self.bounces))
            return True

    def check_offscreen(self):
        return (self.pos[0] - self.radius > Window.width) or \
               (self.pos[0] + self.radius < 0) or \
               (self.pos[1] + self.radius < 0) or \
               (self.pos[1] - self.radius > Window.height)

class PhysicsBubbleHandler(object):
    """
    Handles user interaction and drawing of graphics before generating a PhysicsBubble.
    Also stores and updates all currently active PhysicsBubbles.
    """
    def __init__(self, canvas, mixer, client_id):
        self.canvas = canvas
        self.mixer = mixer
        self.cid = client_id

        self.hold_line = {}
        self.hold_point = {}
        self.hold_shape = {}

        self.color_dict = {
            'red': (255/255, 61/255, 40/255),
            'orange': (252/255, 144/255, 22/255),
            'yellow': (255/255, 255/255, 103/255),
            'green': (146/255, 205/255, 45/255),
            'blue': (71/255, 142/255, 191/255),
            'teal': (86/255, 190/255, 172/255),
            'violet': (143/255, 136/255, 191/255),
            'pink': (248/255, 133/255, 191/255)
        }
        self.pitch_list = [60, 62, 64, 65, 67, 69, 71, 72]

        self.color = {}
        self.pitch = {self.cid: 60}
        self.timbre = {}
        self.bounces = {}

        self.bubbles = AnimGroup()
        self.canvas.add(self.bubbles)

    def on_touch_down(self, cid, pos):
        """
        Start drawing the drag line and preview of the PhysicsBubble.
        """
        self.hold_point[cid] = pos
        self.hold_shape[cid] = CEllipse(cpos=pos, csize=(80, 80))
        self.hold_line[cid] = Line(points=(*pos, *pos), width=3)

        if cid not in self.color:
            self.color[cid] = self.color_dict['red']
        self.canvas.add(Color(*self.color[cid]))

        self.canvas.add(self.hold_shape[cid])
        self.canvas.add(self.hold_line[cid])

    def on_touch_move(self, cid, pos):
        """
        Update the position of the drag line and preview of the PhysicsBubble.
        """
        self.hold_shape[cid].set_cpos(pos)
        self.hold_line[cid].points = (*self.hold_point[cid], *pos)

    def on_touch_up(self, cid, pos):
        """
        Release the PhysicsBubble.
        """
        self.canvas.remove(self.hold_shape[cid])
        self.canvas.remove(self.hold_line[cid])

        hold_point = self.hold_point[cid]
        dx = pos[0] - hold_point[0]
        dy = pos[1] - hold_point[1]
        vel = (-dx, -dy)

        if cid not in self.pitch:
            self.pitch[cid] = self.pitch_list[0]
        pitch = self.pitch[cid]
        color = self.color[cid]

        bubble = PhysicsBubble(pos, vel, pitch, color, callback=self.sound)
        self.bubbles.add(bubble)

    def on_key_down(self, cid, key):
        index = lookup(key, '12345678', range(8))
        color = lookup(key, '12345678', [
            'red', 'orange', 'yellow', 'green', 'blue', 'teal', 'violet', 'pink'
        ])
        if index is not None:
            self.pitch[cid] = self.pitch_list[index]
            self.color[cid] = self.color_dict[color]

    def sound(self, pitch):
        note = NoteGenerator(pitch, 1, 'sine')
        env = Envelope(note, 0.01, 1, 0.2, 2)
        self.mixer.add(env)

    def display_controls(self):
        info = 'pitch: {}'.format(self.pitch[self.cid])
        return info

    def on_update(self):
        self.bubbles.on_update()
