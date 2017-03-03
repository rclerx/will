import pkg_resources
from will.plugin import WillPlugin
from will.decorators import respond_to
import redis
import urlparse
import os
import boto3
import json
from pprint import pformat
from datetime import datetime

class DataAsFile:
    def __init__(self, jsondata):
        self.json = jsondata
    def read(self, *ignored):
        if self.json:
            to_yield = bytes(json.dumps(self.json))
            self.json = None
            return to_yield
        else:
            return bytes()
    # def __enter__(self):
    #     return self
    # def __exit__(self, *args):
    #     return True


class BackupPlugin(WillPlugin):

    def __init__(self):
        url = urlparse.urlparse(os.environ.get('REDISCLOUD_URL'))
        self.redis = redis.Redis(host=url.hostname, port=url.port, password=url.password)

    def _s3(self):
        return boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
        )


    @respond_to("^backup$")
    def help_with_backups(self, message):
        self.say("""Did somebody say backup? To work with backups you can say:
    backup now
    backup list
    backup inspect
    restore [snapshot]
    """, message=message)

    @respond_to("^backup now")
    def take_a_backup(self, message):
        self.say("""No problem, I'll take a backup now.""", message=message)
        urls = self.redis.zrange("pics", 0, -1)
        self.say("/code " + str(pformat(urls)), message=message)
        now = datetime.strftime(datetime.now(), "%F.%H-%M-%S")

        data = DataAsFile(urls)

        s3 = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
        )

        snapshot = 'snapshot-{0}.json'.format(now)
        s3.upload_fileobj(data, 'max.bot', snapshot, ExtraArgs={"ACL": 'public-read'})
        self.say("Done. I saved it as " + snapshot, message=message)

    @respond_to("^backup list")
    def list_backups(self, message):
        self.say("""Sure, I'll get a list of the backups available.""", message=message)
        s3 = self._s3()
        results = s3.list_objects_v2(Bucket="max.bot")
        snapshots = [s['Key'] for s in results['Contents']]
        self.say("""Here they are.""", message=message)
        self.say("/code " + "\n".join(snapshots), message=message)
        self.say("""You can restore one by saying.""", message=message)
        self.say("""/code restore [snapshot]""", message=message)

    @respond_to("^backup inspect (?P<snapshot>snapshot.*json)$")
    def inspect_snapshot(self, message, snapshot):
        self.say("""Let me pull up that backup for you""", message=message)
        s3 = self._s3()
        s3object = s3.get_object(Bucket="max.bot", Key=snapshot)
        body = s3object['Body']

        data = ""
        for line in body.read():
            data += line
        js = json.loads(data)

        self.say("""Here are the images I found in that backup""", message=message)
        self.say("/quote " + "\n".join(js), message=message)

    @respond_to("^restore (?P<snapshot>snapshot.*json)$")
    def restore_snapshot(self, message, snapshot):
        self.say("""Okay, I'm going to restore from """ + snapshot, message=message)
        s3 = self._s3()
        s3object = s3.get_object(Bucket="max.bot", Key=snapshot)
        body = s3object['Body']

        data = ""
        for line in body.read():
            data += line
        pics = json.loads(data)

        self.redis.delete("pics")
        for index, pic in enumerate(pics):
            self.redis.zadd("pics", pic, index)
        self.say("""All set, I've restored from """ + snapshot, message=message)
