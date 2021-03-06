import sys, os
sys.path.insert(0, os.path.abspath('..'))

import requests
import socketio

from common.audio import Audio
from common.core import run, lookup, register_terminate_func
from common.gfxutil import topleft_label, resize_topleft_label
from common.mixer import Mixer
from common.screen import ScreenManager, Screen
from common.writer import AudioWriter
from kivy.core.image import Image
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Rectangle, Line
from kivy.graphics.instructions import InstructionGroup
from kivy.uix.button import Button

from modules.bubble import PhysicsBubble, PhysicsBubbleHandler
from modules.block import SoundBlock, SoundBlockHandler
from modules.cursor import TempoCursor, TempoCursorHandler

server_url = 'http://interval-app.herokuapp.com/'

client = socketio.Client()
client.connect(server_url)
register_terminate_func(client.disconnect)

# each client gets a unique client id upon connecting. we use this client id in many
# functions, especially module handler functions, to make sure all users are synced.
client_id = client.sid

class Normalizer(object):
    def __init__(self, mode):
        self.mode = mode # either 'mac' or 'pc'

    def nt(self, tup):
        return (tup[0]/2, tup[1]/2) if self.mode == 'pc' else tup

    def nv(self, val):
        return val/2 if self.mode == 'pc' else val

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

        mode = 'mac' if (len(sys.argv) == 2) and (sys.argv[1] == 'mac') else 'pc'
        self.norm = Normalizer(mode)

        self.info = topleft_label()
        self.add_widget(self.info)

        self.writer = AudioWriter('recordings/song')
        self.audio = Audio(2, self.writer.add_audio)
        self.mixer = Mixer()
        self.mixer.set_gain(1.0)
        self.audio.set_generator(self.mixer)

        self.sandbox = Sandbox(
            canvas=self.canvas,
            pos=self.norm.nt((580, 50)),
            size=self.norm.nt((1000, 1000))
        )

        # since putting all our sound module code in MainScreen would be a nightmare, we've
        # modularized our modules into separate files. each module has two classes, the sound
        # module itself and its handler class. the handler class is essentially a wrapper of
        # many of MainScreen's important event functions (e.g. on_touch_down) that keeps track
        # of all variables related to that sound module for every connected client.
        self.module_dict = {
            'PhysicsBubble': PhysicsBubble,
            'SoundBlock': SoundBlock,
            'TempoCursor': TempoCursor
        }
        block = SoundBlockHandler(
            self.norm, self.sandbox, self.mixer, client, client_id
        )
        self.module_handlers = {
            'SoundBlock': block,
            'PhysicsBubble': PhysicsBubbleHandler(
                self.norm, self.sandbox, self.mixer, client, client_id, block
            ),
            'TempoCursor': TempoCursorHandler(
                self.norm, self.sandbox, self.mixer, client, client_id, block
            )
        }

        # name a default starting module and handler
        self.module = PhysicsBubble
        self.module_handler = self.module_handlers[self.module.name]
        self.sandbox.add(self.module_handler.gui)

        # sync with existing server state
        client.emit('sync_module_state', {'module': 'PhysicsBubble'})
        client.emit('sync_module_state', {'module': 'SoundBlock'})
        client.emit('sync_module_state', {'module': 'TempoCursor'})
        client.emit('update_norm', {'norm': {client_id: self.norm.mode}})

    def on_touch_down(self, touch):
        if touch.button != 'left':
            return

        global client, client_id
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
        module_name = lookup(key, 'zxc', [
            'PhysicsBubble',
            'SoundBlock',
            'TempoCursor'
        ])
        if module_name is not None:
            old_handler = self.module_handler
            new_handler = self.module_handlers[module_name]
            if old_handler.module_name != new_handler.module_name:
                self.sandbox.remove(old_handler.gui)
                self.sandbox.add(new_handler.gui)
                self.module = self.module_dict[module_name]
                self.module_handler = new_handler
        elif key == 'spacebar':
            print('boop')
            self.writer.toggle()
        else:
            data = {'cid': client_id, 'module': self.module.name, 'key': key}
            client.emit('key_down', data)

    def on_update(self):
        self.audio.on_update()
        for _, handler in self.module_handlers.items():
            handler.on_update()

        self.info.text = 'module: {}\n\n'.format(self.module.name)
        self.info.text += self.module_handler.display_controls()

    def on_layout(self, win_size):
        resize_topleft_label(self.info)

    def update_count(self, count):
        self.count = count

class StartScreen(Screen):
    def __init__(self, **kwargs):
        super(StartScreen, self).__init__(**kwargs)

        self.clicked = False

        self.canvas.add(Color(1,1,1))
        self.logo_size = (300,300)
        self.button_size = (150,75)
        self.img = Rectangle(
            pos=(Window.width/2 - self.logo_size[0]/2, Window.height/2 - 50),
            size=(300,300),
            texture=Image('images/logo.png').texture
        )
        self.create = Rectangle(
            pos=(Window.width/2 - self.button_size[0]/2, Window.height/2 - (325/2)),
            size=(150,75),
            texture=Image('ui/buttons/start-unclicked.png').texture
        )
        self.create_click = Rectangle(
            pos=(Window.width/2 - self.button_size[0]/2, Window.height/2 - (325/2)),
            size=(150,75),
            texture=Image('ui/buttons/start-clicked.png').texture
        )
        self.canvas.add(self.img)
        self.canvas.add(self.create)

    def on_layout(self, win_size):
        self.img.pos = (Window.width/2 - self.logo_size[0]/2, Window.height/2 - 50)
        self.create.pos = (Window.width/2 - self.button_size[0]/2, Window.height/2 - (325/2))
        self.create_click.pos = (Window.width/2 - self.button_size[0]/2, Window.height/2 - (325/2))

    def on_update(self):
        mouse_pos = Window.mouse_pos
        if self.in_bounds(mouse_pos, self.create.pos, self.create.size):
            if self.create_click not in self.canvas.children:
                self.canvas.add(self.create_click)
                return True   
        else:
            if self.create_click in self.canvas.children:
                self.canvas.remove(self.create_click)
                return False

    def on_touch_down(self, touch):
        if self.in_bounds(touch.pos, self.create_click.pos, self.create_click.size):
            self.clicked = True

    def on_touch_up(self, touch):
        if self.in_bounds(touch.pos, self.create_click.pos, self.create_click.size):
            if self.clicked:
                sm.switch_to('main')
        else:
            self.clicked = False

    def in_bounds(self, mouse_pos, button_pos, button_size):
        return (mouse_pos[0] >= button_pos[0]) and \
               (mouse_pos[0] <= button_pos[0] + button_size[0]) and \
               (mouse_pos[1] >= button_pos[1]) and \
               (mouse_pos[1] <= button_pos[1] + button_size[1])

class Sandbox(object):
    def __init__(self, canvas, pos, size):
        self.canvas = canvas
        self.pos = pos
        self.width, self.height = size

        self.border_color = Color(0, 1, 0)
        self.border = Line(rectangle=(*self.pos, self.width, self.height), width=2)
        self.canvas.add(self.border_color)
        self.canvas.add(self.border)

    def add(self, obj):
        self.canvas.add(obj)

    def remove(self, obj):
        self.canvas.remove(obj)

    def in_bounds(self, mouse_pos):
        return (mouse_pos[0] >= self.pos[0]) and \
               (mouse_pos[0] <= self.pos[0] + self.width) and \
               (mouse_pos[1] >= self.pos[1]) and \
               (mouse_pos[1] <= self.pos[1] + self.height)

    def __contains__(self, key):
        return key in self.canvas.children

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
    norm = requests.get('{}norms/{}'.format(server_url, data['cid'])).text
    if main.norm.mode == 'mac' and norm == 'pc':
        pos = (2 * data['pos'][0], 2 * data['pos'][1])
    elif main.norm.mode == 'pc' and norm == 'mac':
        pos = (0.5 * data['pos'][0], 0.5 * data['pos'][1])
    else:
        pos = data['pos']
    module_str = data['module']
    handler = main.module_handlers[module_str]
    handler.on_touch_down(data['cid'], pos)

@client.on('touch_move')
def on_touch_move(data):
    norm = requests.get('{}norms/{}'.format(server_url, data['cid'])).text
    if main.norm.mode == 'mac' and norm == 'pc':
        pos = (2 * data['pos'][0], 2 * data['pos'][1])
    elif main.norm.mode == 'pc' and norm == 'mac':
        pos = (0.5 * data['pos'][0], 0.5 * data['pos'][1])
    else:
        pos = data['pos']
    module_str = data['module']
    handler = main.module_handlers[module_str]
    handler.on_touch_move(data['cid'], pos)

@client.on('touch_up')
def on_touch_up(data):
    norm = requests.get('{}norms/{}'.format(server_url, data['cid'])).text
    if main.norm.mode == 'mac' and norm == 'pc':
        pos = (2 * data['pos'][0], 2 * data['pos'][1])
    elif main.norm.mode == 'pc' and norm == 'mac':
        pos = (0.5 * data['pos'][0], 0.5 * data['pos'][1])
    else:
        pos = data['pos']
    module_str = data['module']
    handler = main.module_handlers[module_str]
    handler.on_touch_up(data['cid'], pos)

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
