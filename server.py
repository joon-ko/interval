import random

from flask import Flask
from flask_socketio import SocketIO, emit
from flask import request

app = Flask(__name__)
socketio = SocketIO(app)

client_count = 0 # number of clients connected

@socketio.on('connect')
def connect():
    global client_count
    client_count += 1

@socketio.on('disconnect')
def disconnect():
    global client_count
    client_count -= 1
    emit('update_count', {'count': client_count}, broadcast=True)

@socketio.on('update_count')
def update_count():
    global client_count
    emit('update_count', {'count': client_count}, broadcast=True)

@socketio.on('sync_state')
def sync_state(data):
    """
    Syncs the state of a new connection with the server's current state for the given module.
    """
    global state_dict
    module_str = data['module']
    server_state = state_dict[module_str]
    emit('sync_state', {'module': module_str, 'state': server_state})

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
        emit('update_state', {'cid': cid, 'state': server_state}, broadcast=True)

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

# We don't sync with hold_shape, hold_point, and hold_line because those objects are not
# json-serializable and are short-term values anyway.
PhysicsBubbleState = {
    'color': {},
    'pitch': {},
    'timbre': {},
    'bounces': {}
}

state_dict = {
    'PhysicsBubble': PhysicsBubbleState
}



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port='8000', debug=True)
