import sys, os
sys.path.insert(0, os.path.abspath('..'))

import requests
import socketio

from common.core import BaseWidget, run, lookup
from common.gfxutil import topleft_label
from kivy.core.window import Window

from modules.bubble import Bubble



server_url = 'http://localhost:5000'
client = socketio.Client()
client.connect(server_url)

@client.on('bubble')
def add_bubble(data):
    widget.add_bubble(data['cpos'])

@client.on('update_count')
def update_count(data):
    widget.update_count(data['count'])



class MainWidget(BaseWidget):
    def __init__(self):
        super(MainWidget, self).__init__()

        self.info = topleft_label()
        self.add_widget(self.info)

        self.response = None
        self.count = 0

        global client
        client.emit('update_count')

    def on_touch_down(self, touch):
        global client
        client.emit('bubble', {'cpos': touch.pos})

    def on_key_down(self, keycode, modifiers):
        pass

    def on_update(self):
        self.info.text = '# connected: {}'.format(self.count)

    def on_close(self):
        # disconnect the client before kivy shuts down to prevent hanging connections.
        global client
        client.disconnect()

    def add_bubble(self, cpos):
        bubble = Bubble(cpos)
        self.canvas.add(bubble)

    def update_count(self, count):
        self.count = count

if __name__ == "__main__":
    # we need an instance of MainWidget() to make handling socket events easier.
    # run() in core.py has been modified as a consequence.
    widget = MainWidget()
    run(widget)
