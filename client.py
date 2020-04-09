import sys, os
sys.path.insert(0, os.path.abspath('..'))

import requests
import socketio

from common.core import BaseWidget, run, lookup
from common.gfxutil import topleft_label
from kivy.core.window import Window

from modules.bubble import PhysicsBubble, PhysicsBubbleHandler



server_url = 'http://173.52.37.59:8000/'
client = socketio.Client()
client.connect(server_url)
client_id = client.sid

@client.on('update_count')
def update_count(data):
    widget.update_count(data['count'])

@client.on('on_touch_down')
def on_touch_down(data):
    module_str = data['module']
    handler = widget.module_handlers[module_str]
    handler.on_touch_down(data['cid'], data['pos'])

@client.on('on_touch_move')
def on_touch_move(data):
    module_str = data['module']
    handler = widget.module_handlers[module_str]
    handler.on_touch_move(data['cid'], data['pos'])

@client.on('on_touch_up')
def on_touch_up(data):
    module_str = data['module']
    handler = widget.module_handlers[module_str]
    handler.on_touch_up(data['cid'], data['pos'])



class MainWidget(BaseWidget):
    def __init__(self):
        super(MainWidget, self).__init__()

        self.info = topleft_label()
        self.add_widget(self.info)

        self.response = None
        self.count = 0

        global client
        client.emit('update_count')

        self.module_dict = {
            'PhysicsBubble': PhysicsBubble,
        }
        self.module_handlers = {
            'PhysicsBubble': PhysicsBubbleHandler(self.canvas),
        }

        # name a default starting module and handler
        self.module = PhysicsBubble
        self.module_handler = self.module_handlers[self.module.name]

    def on_touch_down(self, touch):
        global client, client_id
        # we send touch.pos instead because touch isn't json-serializable
        data = {'cid': client_id, 'module': self.module.name, 'pos': touch.pos}
        client.emit('on_touch_down', data)

    def on_touch_move(self, touch):
        global client, client_id
        data = {'cid': client_id, 'module': self.module.name, 'pos': touch.pos}
        client.emit('on_touch_move', data)

    def on_touch_up(self, touch):
        global client, client_id
        data = {'cid': client_id, 'module': self.module.name, 'pos': touch.pos}
        client.emit('on_touch_up', data)

    def on_key_down(self, keycode, modifiers):
        global client
        key = keycode[1]

        # switch module using number keys
        module_name = lookup(key, '1', [
            'PhysicsBubble'
        ])
        if module_name is not None:
            self.module = self.module_dict[module_name]
            self.module_handler = self.module_handlers[module_name]

    def on_update(self):
        for _, handler in self.module_handlers.items():
            handler.on_update()

        self.info.text = '# connected: {}\n'.format(self.count)
        self.info.text += 'module: {}\n'.format(self.module.name)

    def on_close(self):
        # disconnect the client before kivy shuts down to prevent hanging connections.
        global client
        client.disconnect()

    def update_count(self, count):
        self.count = count

if __name__ == "__main__":
    # we need an instance of MainWidget() to make handling socket events easier.
    # run() in core.py has been modified as a consequence.
    widget = MainWidget()
    run(widget)
