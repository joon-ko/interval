import random
import os

from flask import Flask
from flask_socketio import SocketIO, emit
from flask import request

# attempt to fix packet 'too many packets in payload' error
from engineio.payload import Payload
Payload.max_decode_packets = 500

app = Flask(__name__)
socketio = SocketIO(app)

client_count = 0 # number of clients connected

@app.route('/')
def test_online():
    return 'server online!'

@app.route('/norms/<cid>')
def get_norms(cid):
    return state_dict['norm'].get(cid)

@socketio.on('connect')
def connect():
    """This function is run every time a new client connects to the server."""
    global client_count
    client_count += 1

@socketio.on('disconnect')
def disconnect():
    global client_count
    client_count -= 1

@socketio.on('sync_module_state')
def sync_module_state(data):
    """
    Syncs the state of a new connection with the server's current state for the given module.
    """
    global state_dict
    module_str = data['module']
    server_state = state_dict[module_str]
    emit('sync_module_state', {'module': module_str, 'state': server_state})

@socketio.on('update_state')
def update_state(data):
    """
    Updates the server's state after a module handler updates their state.
    Optionally relays this updated state to all clients if data['post'] is True.
    """
    global state_dict
    module_str, client_state, cid, post = data['module'], data['state'], data['cid'], data['post']
    server_state = state_dict[module_str]
    server_state.update(client_state)

    if post:
        send_data = {'cid': cid, 'module': module_str, 'state': server_state}
        emit('update_state', send_data, broadcast=True)

@socketio.on('update_norm')
def update_norm(data):
    global state_dict
    state_dict['norm'].update(data['norm'])

@socketio.on('touch_down')
def on_touch_down(data):
    emit('touch_down', data, broadcast=True)

@socketio.on('touch_move')
def on_touch_move(data):
    emit('touch_move', data, broadcast=True)

@socketio.on('touch_up')
def on_touch_up(data):
    emit('touch_up', data, broadcast=True)

@socketio.on('key_down')
def on_key_down(data):
    emit('key_down', data, broadcast=True)


###################
# state variables #
###################

# we don't sync with hold_shape, hold_point, and hold_line because those objects are not
# json-serializable and are short-term values anyway.
PhysicsBubbleState = {
    'color': {},
    'pitch': {},
    'timbre': {},
    'bounces': {},
    'gravity': {}
}
SoundBlockState = {
    'color': {},
    'pitch': {},
    'timbre': {},
    'instrument': {},
    'drum': {},
    'delete_mode': {}
}
TempoCursorState = {
    'touch_points': {},
    'delete_mode': {},
    'tempo': 60
}

state_dict = {
    'PhysicsBubble': PhysicsBubbleState,
    'SoundBlock': SoundBlockState,
    'TempoCursor': TempoCursorState,
    'norm': {}
}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
