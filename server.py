import random

from flask import Flask
from flask_socketio import SocketIO, emit
from flask import request

app = Flask(__name__)
socketio = SocketIO(app)

client_count = 0 # number of clients connected

@app.route('/randint')
def test_random():
    return str(random.randint(0, 10))

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



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port='8000', debug=True)
