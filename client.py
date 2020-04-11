import sys, os
sys.path.insert(0, os.path.abspath('..'))

import requests
import socketio

from common.audio import Audio
from common.core import BaseWidget, run, lookup
from common.gfxutil import topleft_label, resize_topleft_label
from common.mixer import Mixer
from kivy.core.window import Window

from modules.bubble import PhysicsBubble, PhysicsBubbleHandler



server_url = 'http://173.52.37.59:8000/'
client = socketio.Client()
client.connect(server_url)
client_id = client.sid

class MainWidget(BaseWidget):
    def __init__(self):
        super(MainWidget, self).__init__()

        self.info = topleft_label()
        self.add_widget(self.info)

        self.response = None
        self.count = 0

        self.audio = Audio(2)
        self.mixer = Mixer()
        self.mixer.set_gain(1.0)
        self.audio.set_generator(self.mixer)

        global client, client_id
        client.emit('update_count')

        self.module_dict = {
            'PhysicsBubble': PhysicsBubble,
        }
        self.module_handlers = {
            'PhysicsBubble': PhysicsBubbleHandler(self.canvas, self.mixer, client_id),
        }

        # name a default starting module and handler
        self.module = PhysicsBubble
        self.module_handler = self.module_handlers[self.module.name]

    def on_touch_down(self, touch):
        if touch.button != 'left':
            return

        global client, client_id
        # we send touch.pos instead because touch isn't json-serializable
        data = {'cid': client_id, 'module': self.module.name, 'pos': touch.pos}
        client.emit('touch_down', data)

    def on_touch_move(self, touch):
        if touch.button != 'left':
            return

        global client, client_id
        data = {'cid': client_id, 'module': self.module.name, 'pos': touch.pos}
        client.emit('touch_move', data)

    def on_touch_up(self, touch):
        if touch.button != 'left':
            return

        global client, client_id
        data = {'cid': client_id, 'module': self.module.name, 'pos': touch.pos}
        client.emit('touch_up', data)

    def on_key_down(self, keycode, modifiers):
        global client, client_id
        key = keycode[1]

        # switch module using keys (for now)
        module_name = lookup(key, 'q', [
            'PhysicsBubble'
        ])
        if module_name is not None:
            self.module = self.module_dict[module_name]
            self.module_handler = self.module_handlers[module_name]
        else:
            data = {'cid': client_id, 'module': self.module.name, 'key': key}
            client.emit('key_down', data)

    def on_update(self):
        self.audio.on_update()
        for _, handler in self.module_handlers.items():
            handler.on_update()

        self.info.text = '# connected: {}\n'.format(self.count)
        self.info.text += 'module: {}\n'.format(self.module.name)
        self.info.text += self.module_handler.display_controls()

    def on_layout(self, win_size):
        resize_topleft_label(self.info)

    def on_close(self):
        # disconnect the client before kivy shuts down to prevent hanging connections.
        global client
        client.disconnect()

    def update_count(self, count):
        self.count = count

@client.on('update_count')
def update_count(data):
    widget.update_count(data['count'])

@client.on('touch_down')
def on_touch_down(data):
    module_str = data['module']
    handler = widget.module_handlers[module_str]
    handler.on_touch_down(data['cid'], data['pos'])

@client.on('touch_move')
def on_touch_move(data):
    module_str = data['module']
    handler = widget.module_handlers[module_str]
    handler.on_touch_move(data['cid'], data['pos'])

@client.on('touch_up')
def on_touch_up(data):
    module_str = data['module']
    handler = widget.module_handlers[module_str]
    handler.on_touch_up(data['cid'], data['pos'])

@client.on('key_down')
def on_key_down(data):
    module_str = data['module']
    handler = widget.module_handlers[module_str]
    handler.on_key_down(data['cid'], data['key'])

if __name__ == "__main__":
    # we need an instance of MainWidget() to make handling socket events easier.
    # run() in core.py has been modified as a consequence.
    widget = MainWidget()
    run(widget)
