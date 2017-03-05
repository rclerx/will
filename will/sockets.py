#!/usr/bin/env python
#
# Courtesy of https://blog.miguelgrinberg.com/post/easy-websockets-with-flask-and-gevent
#
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from flask import Flask, render_template, session, request
import settings
import logging
import os
import json
import redis
import urlparse
from pprint import pformat


logger = logging.getLogger(__name__)

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

from will.webapp import app
socketio = SocketIO(app, async_mode=async_mode)
thread = None


def get_socketio_app():
    # This is the key to starting the socketio app.
    # It runs as a wrapper around Flask. See webapp.bootstrap_flask().
    return socketio


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    REDIS_CHANNELS = ['updates']

    url = urlparse.urlparse(os.environ.get('REDISCLOUD_URL'))
    r = redis.Redis(host=url.hostname, port=url.port, password=url.password)
    pubsub = r.pubsub()
    pubsub.subscribe(REDIS_CHANNELS)

    logger.info("Starting the redis pubsub listener ...")
    while True:
        message = pubsub.get_message() # SDG!
        if message:
            logger.info(u'pubsub saw this message: {}'.format(pformat(message)))
            try:
                data = json.loads(message.get('data'))
                socketio.emit('my_picture', data, namespace='/max', broadcast=True)
                logger.info(u'Sent that new pic for clients: {}'.format(pformat(data)))
            except Exception as e:
                logger.warn("That didn't appear to be JSON so I didn't forward it")

        socketio.sleep(0.01)

    logger.info("Redis pubsub over and out!")


@app.route('/sox')
def index():
    return render_template('sockets.html', async_mode=socketio.async_mode)


@socketio.on('my_event', namespace='/max')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.on('my_broadcast_event', namespace='/max')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socketio.on('join', namespace='/max')
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('leave', namespace='/max')
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('close_room', namespace='/max')
def close(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         room=message['room'])
    close_room(message['room'])


@socketio.on('my_room_event', namespace='/max')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         room=message['room'])


@socketio.on('disconnect_request', namespace='/max')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()


@socketio.on('my_ping', namespace='/max')
def ping_pong():
    emit('my_pong')


@socketio.on('connect', namespace='/max')
def test_connect():
    global thread
    if thread is None:
        thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/max')
def test_disconnect():
    print('Client disconnected', request.sid)


if __name__ == '__main__':
    socketio.run(app, debug=True)
