from will.plugin import WillPlugin
from will.decorators import respond_to, periodic, hear, randomly, route, rendered_template, require_settings
import re
import logging
import requests
from will import settings


logger = logging.getLogger(__name__)


class WhoPlugin(WillPlugin):

    @respond_to("who are you")
    def say_bonjour_will(self, message):
        """who are you: name and serial number"""
        self.reply(message, "Hello. I am Baymax, your personal healthcare companion. On a scale of one to ten, how would you rate your pain?")

    @respond_to("^http|: http")
    def pic(self, message):
        """SDG!"""
        pattern = re.compile("(http.*(jpg|png|gif))")
        matches = pattern.search(message['body'])
        if matches and matches.group():
            payload = {"image": matches.group()}
            logger.info("Posting to " + settings.GALLERY_URL + " with body " + str(message['body']) + " and payload " + str(payload))
            r = requests.post(settings.GALLERY_URL, data=payload)
            self.reply(message, "Got it!")

    @respond_to("^.")
    def other(self, message):
        logger.info("I heard something '" + str(message['body']) + "'")
