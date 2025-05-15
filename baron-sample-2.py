import requests
import datetime
import simplejson as json
import mimetypes
import hashlib
import base64
import os
import hmac
import time
from dotenv import load_dotenv

load_dotenv("local.env")
access_key = os.getenv("BARON_KEY")
if access_key is None:
    raise ValueError("Missing BARON_KEY in local.env file")
access_key_secret = os.getenv("BARON_SECRET")
if access_key_secret is None:
    raise ValueError("Missing BARON_SECRET in local.env file")


def wx_sign_url(url, key, secret):
    def wx_sign(data, secret):
        return base64.urlsafe_b64encode(hmac.new(secret.encode('utf-8'), data.encode('utf-8'), hashlib.sha1).digest())

    timestamp = "%.0f" % (time.time())

    signature = wx_sign(key + ":" + timestamp, secret)

    if url.find("?") == -1:
        url += ("?sig=%s&ts=%s" % (signature, timestamp))
    else:
        url += ("&sig=%s&ts=%s" % (signature, timestamp))

    return url


class APIClient(object):
    def __init__(self, key, secret, base="http://localhost:80/v1"):
        self.base = base
        self.key = key
        self.secret = secret

    def make_url(self, api):
        url = "%s/%s%s" % (self.base, self.key, api)
        return wx_sign_url(url, self.key, self.secret)

    def query_instances(self, product, configuration, before=None):

        # print "\nQuery {} {}".format(product,configuration)

        if before:
            url = self.make_url(
                "/meta/tiles/product-instances/{}/{}.json?limit=10&older_than={}".format(product, configuration, before))
        else:
            url = self.make_url(
                "/meta/tiles/product-instances/{}/{}.json?limit=10".format(product, configuration))

        print(url)

        return requests.get(url).json()

    def list_all_instances(self, product, configuration):

        instances = self.query_instances(product, configuration)

        while instances:
            for instance in instances:
                print(instance)

            print(instances[-1]['time'])

            instances = self.query_instances(
                product, configuration, instances[-1]['time'])

            # instances = None

    def query_geotiff(self, product, configuration, time):

        url = self.make_url(
            "/geotiff/{}/{}/{}.json".format(product, configuration, time))

        print(url)

        result = requests.get(url)

        # print result.json()

        print(json.dumps(result.json(), sort_keys=True, indent=4))


user = APIClient(key=access_key, secret=access_key_secret,
                 base="http://api.velocityweather.com/v1")


instances = user.query_instances('C39-0x0302-0', 'Standard-Mercator')

print(instances)

user.query_geotiff('C39-0x0302-0', 'Standard-Mercator', instances[0]['time'])
