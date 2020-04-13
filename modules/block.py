import sys, os
sys.path.insert(0, os.path.abspath('..'))

from kivy.graphics.instructions import InstructionGroup

class SoundBlock(InstructionGroup):
	"""
	This module is a rectangular, static block that plays a sound when either someone clicks it,
	or another sound module (e.g. PhysicsBubble) collides with it.
	"""
	name = 'SoundBlock'

	def __init__(self):
		pass

class SoundBlockHandler(object):
	"""
	Handles user interaction and drawing of graphics before generating a SoundBlock.
    Also stores and updates all currently active SoundBlocks.
	"""
	def __init__(self, canvas, mixer, client, client_id):
		self.module_name = 'SoundBlock'
		self.canvas = canvas
		self.mixer = mixer
		self.client = client
		self.cid = client_id

	def on_touch_down(self, cid, pos):
		pass

	def on_touch_move(self, cid, pos):
		pass

	def on_touch_up(self, cid, pos):
		pass

	def on_key_down(self, cid, key):
		pass

	def display_controls(self):
		return 'this module\'s info coming soon!'

	def on_update(self):
		pass
