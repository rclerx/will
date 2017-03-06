from will.plugin import WillPlugin
from will.decorators import respond_to, periodic, hear, randomly, route, rendered_template, require_settings
import re
import logging
import requests
from will import settings


logger = logging.getLogger(__name__)


class PhotoPlugin(WillPlugin):

    """SDG!"""

    @respond_to("^http|: http")
    def pic(self, message):
        """Send me a picture with: @max http://my.net/pic.jpg
        Or send it to me in a private message.
        You can also use the keyboard to control the slideshow:
        > Backspace to remove the current slide
        > Left/right arrows to move forward and back
        > Spacebar to pause and resume
        """
        pattern = re.compile("(http.*(jpg|png|gif))", re.IGNORECASE)
        matches = pattern.search(message['body'])
        if matches and matches.group():
            payload = {"image": matches.group()}
            logger.info("Posting to " + settings.GALLERY_URL + " with body " + str(message['body']) + " and payload " + str(payload))
            r = requests.post(settings.GALLERY_URL, data=payload)
            self.reply(message, "Got it!")


    @respond_to("^what's new")
    def other(self, message):
        logger.info("Now you can send me photos in a private message and I'll post them to the slideshow. (https://album-sse.herokuapp.com)")


    @respond_to("^.")
    def other(self, message):
        logger.info("I heard something ... '" + str(message['body']) + "'")
