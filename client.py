import sys, os
sys.path.insert(0, os.path.abspath('..'))

import requests
import socketio

from common.audio import Audio
from common.core import run, lookup
from common.gfxutil import topleft_label, resize_topleft_label
from common.mixer import Mixer
from common.screen import ScreenManager, Screen
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Rectangle, Line

from modules.bubble import PhysicsBubble, PhysicsBubbleHandler
from modules.block import SoundBlock, SoundBlockHandler

from kivy.uix.button import Button
from kivy.core.image import Image

server_url = 'http://localhost:8000'
client = socketio.Client()
client.connect(server_url)

# each client gets a unique client id upon connecting. we use this client id in many
# functions, especially module handler functions, to make sure all users are synced.
client_id = client.sid

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

        self.info = topleft_label()
        self.add_widget(self.info)

        self.count = 0 # total number of connected clients

        self.audio = Audio(2)
        self.mixer = Mixer()
        self.mixer.set_gain(1.0)
        self.audio.set_generator(self.mixer)

        global client, client_id
        client.emit('update_count') # get the updated number of connected clients

        # since putting all our sound module code in MainScreen would be a nightmare, we've
        # modularized our modules into separate files. each module has two classes, the sound
        # module itself and its handler class. the handler class is essentially a wrapper of
        # many of MainScreen's important event functions (e.g. on_touch_down) that keeps track
        # of all variables related to that sound module for every connected client.
        self.module_dict = {
            'PhysicsBubble': PhysicsBubble,
            'SoundBlock': SoundBlock
        }
        self.module_handlers = {
            'PhysicsBubble': PhysicsBubbleHandler(self.canvas, self.mixer, client, client_id),
            'SoundBlock': SoundBlockHandler(self.canvas, self.mixer, client, client_id)
        }

        # name a default starting module and handler
        self.module = PhysicsBubble
        self.module_handler = self.module_handlers[self.module.name]

        # sync with existing server state
        client.emit('sync_module_state', {'module': self.module.name})

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
        module_name = lookup(key, 'zx', [
            'PhysicsBubble',
            'SoundBlock'
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
        # possibly look into using core.py's register_terminate_func() instead?
        global client
        client.disconnect()

    def update_count(self, count):
        self.count = count

def in_bounds(mouse_pos, button_pos, button_size):
    if mouse_pos[0] >= (button_pos[0]): #lower x bound
        if mouse_pos[0] <= (button_pos[0] + button_size[0]): #upper x bound
            if mouse_pos[1] >= (button_pos[1]): #lower y bound
                if mouse_pos[1] <= (button_pos[1] + button_size[1]): #upper x bound
                    return True
    return False

class StartScreen(Screen):
    def __init__(self, **kwargs):
        super(StartScreen, self).__init__(**kwargs)

        #self.create = Button(text='Create Room', font_size=15, pos = (Window.width/2 - 50, Window.height/2 - 175))
        #self.create.bind(on_release= lambda x: self.switch_to('main'))
        #self.add_widget(self.create)

        self.canvas.add(Color(1,1,1))
        self.img = Rectangle(pos=(Window.width/2 - 150, Window.height/2), size=(300,300), texture=Image('logo.png').texture)
        self.create = Rectangle(pos=(Window.width/2 - 75, Window.height/2 - (325/2)), size=(150,75), texture=Image('ui/buttons/start-unclicked.png').texture)
        self.create_click = Rectangle(pos=(Window.width/2 - 75, Window.height/2 - (325/2)), size=(150,75), texture=Image('ui/buttons/start-clicked.png').texture)
        self.canvas.add(self.img)
        self.canvas.add(self.create)

    def on_layout(self, win_size):
        self.img.pos = (Window.width/2 - 150, Window.height/2 - 50) 
        self.create.pos = (Window.width/2 - 75, Window.height/2 - (325/2))
        if self.create_click in self.children:
            self.create_click.pos = (Window.width/2 - 75, Window.height/2 - (325/2))

    def on_update(self):
        mouse_pos = Window.mouse_pos
        #print("MOUSE POS ", mouse_pos, " POS ", self.create.pos, " x BUF ", self.create.size[0]/2, " Y BUF ", self.create.size[1]/2)
        if in_bounds(mouse_pos, self.create.pos, self.create.size):
            self.canvas.add(self.create_click)
            return True   
        else:
            if self.create_click in self.canvas.children:
                self.canvas.remove(self.create_click)
                return False

    def on_touch_down(self, touch):
        if in_bounds(touch.pos, self.create_click.pos, self.create_click.size):
            self.switch_to('main')

@client.on('update_count')
def update_count(data):
    main.update_count(data['count'])

@client.on('sync_module_state')
def sync_module_state(data):
    module_str = data['module']
    handler = main.module_handlers[module_str]
    handler.sync_state(data['state'])

@client.on('update_state')
def update_client_state(data):
    module_str, state, cid = data['module'], data['state'], data['cid']
    handler = main.module_handlers[module_str]
    handler.update_client_state(cid, state)

@client.on('touch_down')
def on_touch_down(data):
    module_str = data['module']
    handler = main.module_handlers[module_str]
    handler.on_touch_down(data['cid'], data['pos'])

@client.on('touch_move')
def on_touch_move(data):
    module_str = data['module']
    handler = main.module_handlers[module_str]
    handler.on_touch_move(data['cid'], data['pos'])

@client.on('touch_up')
def on_touch_up(data):
    module_str = data['module']
    handler = main.module_handlers[module_str]
    handler.on_touch_up(data['cid'], data['pos'])

@client.on('key_down')
def on_key_down(data):
    module_str = data['module']
    handler = main.module_handlers[module_str]
    handler.on_key_down(data['cid'], data['key'])

if __name__ == "__main__":
    sm = ScreenManager()
    start = StartScreen(name='start')
    main = MainScreen(name='main')
    sm.add_screen(start)
    sm.add_screen(main)
    run(sm)
