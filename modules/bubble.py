import sys, os
sys.path.insert(0, os.path.abspath('..'))

from common.gfxutil import topleft_label, CEllipse, AnimGroup
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

    def __init__(self, pos, vel):
        super(PhysicsBubble, self).__init__()

        self.r = 25
        self.pos = np.array(pos, dtype=np.float)
        self.vel = 2 * np.array(vel, dtype=np.float)

        self.color = Color(0, 1, 0)
        self.add(self.color)

        self.bubble = CEllipse(cpos=pos, csize=(50, 50))
        self.add(self.bubble)

        self.on_update(0)

    def on_update(self, dt):
        self.pos += self.vel * dt
        self.check_for_collisions()
        self.bubble.set_cpos(self.pos)
        return True

    def check_for_collisions(self):
        # collision with bottom
        if self.pos[1] - self.r < 0:
            self.vel[1] = -self.vel[1]
            self.pos[1] = self.r

        # collision with top
        if self.pos[1] + self.r > Window.height:
            self.vel[1] = -self.vel[1]
            self.pos[1] = Window.height - self.r

        # collision with left
        if self.pos[0] - self.r < 0:
            self.vel[0] = -self.vel[0]
            self.pos[0] = self.r

        # collision with right
        if self.pos[0] + self.r > Window.width:
            self.vel[0] = -self.vel[0]
            self.pos[0] = Window.width - self.r

class PhysicsBubbleHandler(object):
    """
    Handles user interaction and drawing of graphics before generating a PhysicsBubble.
    Also stores and updates all currently active PhysicsBubbles.
    """
    def __init__(self, canvas):
        self.canvas = canvas

        self.client_ids = []

        self.hold_lines = {}
        self.hold_points = {}
        self.hold_shapes = {}
        self.colors = {}

        self.bubbles = AnimGroup()
        self.canvas.add(self.bubbles)

    def on_touch_down(self, cid, pos):
        """
        Start drawing the drag line and preview of the PhysicsBubble.
        """
        self.hold_points[cid] = pos
        self.hold_shapes[cid] = CEllipse(cpos=pos, csize=(50, 50))
        self.hold_lines[cid] = Line(points=(*pos, *pos), width=2)
        self.colors[cid] = Color(1, 1, 1)

        self.canvas.add(self.colors[cid])
        self.canvas.add(self.hold_shapes[cid])
        self.canvas.add(self.hold_lines[cid])

    def on_touch_move(self, cid, pos):
        """
        Update the position of the drag line and preview of the PhysicsBubble.
        """
        self.hold_shapes[cid].set_cpos(pos)
        self.hold_lines[cid].points = (*self.hold_points[cid], *pos)

    def on_touch_up(self, cid, pos):
        """
        Release the PhysicsBubble.
        """
        self.canvas.remove(self.hold_shapes[cid])
        self.canvas.remove(self.hold_lines[cid])

        # calculate velocity
        hold_point = self.hold_points[cid]
        dx = pos[0] - hold_point[0]
        dy = pos[1] - hold_point[1]
        vel = (-dx, -dy)

        bubble = PhysicsBubble(pos, vel)
        self.bubbles.add(bubble)

    def on_update(self):
        self.bubbles.on_update()
