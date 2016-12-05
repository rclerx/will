import pkg_resources
from will.plugin import WillPlugin
from will.decorators import respond_to
import socket

class VersionPlugin(WillPlugin):

    @respond_to("^version$")
    def say_version(self, message):
        version = pkg_resources.get_distribution("will").version
        self.say("I'm running version %s from %s" % (version, socket.gethostname()), message=message)
