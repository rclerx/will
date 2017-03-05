import requests
from will.plugin import WillPlugin
from will.decorators import respond_to, periodic, hear, randomly, route, rendered_template, require_settings
from will import settings

keep_alive_url = "/keep-alive"


class KeepAlivePlugin(WillPlugin):

    @periodic(second=0)
    @require_settings("PUBLIC_URL",)
    def ping_keep_alive(self):
        requests.get("%s%s" % (settings.PUBLIC_URL, keep_alive_url))
