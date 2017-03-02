#!/usr/bin/env python
#
# export REDISCLOUD_URL=redis://localhost:6379/7
# FLASK_APP=manage.py flask run
# FLASK_DEBUG=1 python manage.py runserver
# gunicorn manage:app

from flask_script import Server, Manager
from flask import Flask
from flask import jsonify
from flask import send_from_directory
from flask import request
from flask import render_template
from flask_sockets import Sockets
from pprint import pformat
import os
import time
import json
import urlparse
import redis
import logging
import gevent
import settings


# logging.basicConfig(
#     level=logging.INFO,
#     format='%(levelname)-8s %(message)s'
# )
logger = logging.getLogger(__name__)

url = urlparse.urlparse(os.environ.get('REDISCLOUD_URL'))
r = redis.Redis(host=url.hostname, port=url.port, password=url.password)
pubsub = redis.Redis(host=url.hostname, port=url.port, password=url.password)


logger.info("type of pics is " + r.type("pics"))

if not r.exists("pics"):
    # First ever startup -- load some default images
    defaultpics = [
        "https://s3.amazonaws.com/uploads.hipchat.com/398524/2959249/Fv0U8jU47Z1RWQt/20151211_235234.jpg",
        "https://s3.amazonaws.com/uploads.hipchat.com/398524/2973098/mX8h75W4A17wm8a/upload.jpg",
        "https://s3.amazonaws.com/uploads.hipchat.com/398524/2856310/qwTHxLZQA1uVrEw/upload.png",
        "https://s3.amazonaws.com/uploads.hipchat.com/398524/2973989/YTonrDGuXGngIDM/upload.png"]

    now = time.time()
    for index, pic in enumerate(defaultpics):
        r.zadd("pics", pic, now - index)

elif r.type("pics") == "list":
    # Data migration from list to sorted-set
    all = [p for p in r.lrange("pics", 0, -1)]
    r.delete("pics")
    for index, pic in enumerate(all):
        r.zadd("pics", pic, index+1)



REDIS_CHAN = 'updates'

class PicsBackend(object):
    """Interface for registering and updating WebSocket clients."""

    def __init__(self):
        self.clients = list()
        self.pubsub = pubsub.pubsub()
        self.pubsub.subscribe(REDIS_CHAN)

    def __iter_data(self):
        for message in self.pubsub.listen():
            data = message.get('data')
            if message['type'] == 'message':
                #app.logger.info(u'Got a new pic for clients: {}'.format(data))
                logger.info(u'Got a new pic for clients: {}'.format(data))
                yield data

    def register(self, client):
        """Register a WebSocket connection for Redis updates."""
        #app.logger.info(u'Registering connected client')
        logger.info(u'Registering connected client')
        self.clients.append(client)

    def send(self, client, data):
        """Send given data to the registered client.
        Automatically discards invalid connections."""
        try:
            client.send(data)
        except Exception:
            self.clients.remove(client)

    def run(self):
        """Listens for new messages in Redis, and sends them to clients."""
        logger.info("Running subscriber")
        for data in self.__iter_data():
            for client in self.clients:
                gevent.spawn(self.send, client, data)

    def start(self):
        """Maintains Redis subscription in the background."""
        logger.info("Starting subscriber")
        gevent.spawn(self.run)


app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'), static_url_path='/static')
sockets = Sockets(app)
backend = PicsBackend()


def bootstrap_flask():
    logger.info("Starting flask server on port " + settings.HTTPSERVER_PORT)
    app.run(host="0.0.0.0", port=settings.HTTPSERVER_PORT)

def bootstrap_websockets():
    logger.info("Starting websockets")



@app.route('/')
def slideshow():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'static'), "slideshow.html")


@app.route('/pics', methods=['GET'])
def pics():
    logger.info("Handling GET /pics with " + request.method)
    logger.info("  Headers:" + pformat(request.headers))
    logger.info("  Form:   " + pformat(request.form))
    logger.info("  Data:   " + pformat(request.data))
    # Get photo URLs from Redis
    urls = r.zrange("pics", 0, -1)
    return jsonify(list(reversed(urls)))


@app.route('/pics', methods=['POST'])
def add_pic():
    image = request.form['image']
    if image:
        logger.info("Publishing new image: " + image)
        logger.info(pformat(request.form))
        r.zadd("pics", image, time.time())
        pubsub.publish(REDIS_CHAN, json.dumps(image))
        return jsonify([image])
    else:
        return jsonify([])


@app.route('/pics', methods=['DELETE'])
def delete_pic():
    image = request.form['image']
    logger.info("Deleting pic:  " + image)
    r.zrem("pics", image)
    return jsonify("deleted " + image)


@app.route('/reset')
def reset_pics():
    r.delete("pics")
    return "Pics have been reset"


@sockets.route('/updates')
def realtime_updates(ws):
    """Sends outgoing pic updates, via `PicsBackend`."""
    backend.register(ws)

    while not ws.closed:
        # Context switch while `ChatBackend.start` is running in the background.
        gevent.sleep(0.1)


if __name__ == "__main__":
    manager.run()

