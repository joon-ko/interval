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

        self.color = Color(1, 1, 1)
        self.canvas.add(self.color)
        self.hold_line = None
        self.hold_point = None
        self.hold_shape = None

        self.bubbles = AnimGroup()
        self.canvas.add(self.bubbles)

    def on_touch_down(self, pos):
        """
        Start drawing the drag line and preview of the PhysicsBubble.
        """
        self.color.rgb = (1, 1, 1)
        self.canvas.add(self.color)
        self.hold_point = pos
        self.hold_shape = CEllipse(cpos=pos, csize=(50, 50))
        self.hold_line = Line(points=(*pos, *pos), width=2)
        self.canvas.add(self.hold_shape)
        self.canvas.add(self.hold_line)

    def on_touch_move(self, pos):
        """
        Update the position of the drag line and preview of the PhysicsBubble.
        """
        self.hold_shape.set_cpos(pos)
        self.hold_line.points = (*self.hold_point, *pos)

    def on_touch_up(self, pos):
        """
        Release the PhysicsBubble.
        """
        self.canvas.remove(self.hold_shape)
        self.canvas.remove(self.hold_line)
        self.hold_shape = None
        self.hold_line = None

        # calculate velocity
        dx = pos[0] - self.hold_point[0]
        dy = pos[1] - self.hold_point[1]
        vel = (-dx, -dy)
        self.hold_point = None

        bubble = PhysicsBubble(pos, vel)
        self.bubbles.add(bubble)

    def on_update(self):
        self.bubbles.on_update()
