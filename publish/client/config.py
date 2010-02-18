"""
Configuration class for Publication Service

Instantiation of this class will create ~/.lulu_publish_api.conf if it does not already
exist.   Users will then have to enter in the /correct/ values for the server
in order to use it.

Reasonable values are:

auth_server: 'api1.lulu.com'
publish_api_server:  'api1.lulu.com'
user: 'your-email@example.org'
key: 'your-password-here'

"""

import ConfigParser
import os
import sys

LOCAL_CONF = os.path.expanduser("~/.lulu_publish_api.conf")

# FIXME: for release, change these to api{1,2}.lulu.com
CONFIG_DEFAULTS = """
# Configuration file for Lulu Publication client library

[server]
auth_server = 127.0.0.1
publish_api_server = 127.0.0.1

[credentials]
user = user@example.org
key = password_here
"""

class Config:

    def __init__(self):
        """
        The configuration class will default to the values in ~/.lulu_publish_api.conf
        if it exists, if not, it will create the file.
        """
        self.parser = ConfigParser.ConfigParser()
        if os.path.exists(LOCAL_CONF):
            fp = open(LOCAL_CONF)
            self.parser.readfp(fp)
            fp.close()
        else:
            # NOTE: this default config has various default values that are not usable
            # so the get methods below will cause API failures further down the line once
            # actually used.
            fd = open(LOCAL_CONF, "w+")
            fd.write(CONFIG_DEFAULTS)
            fd.close()

    def get_auth_server(self):
        """
        Connect to this server for all db requests
        """
        return self.parser.get("server", "auth_server", "127.0.0.1")

    def get_publish_api_server(self):
        """
        Where is the PHP authentication endpoint?
        """
        return self.parser.get("server", "publish_api_server", "127.0.0.1")

    def get_user(self):
        """
        Is the user password saved?
        """
        user = self.parser.get("credentials", "user", None)
        if user == "user@example.org":
            raise Exception("User needs to be changed in %s" % LOCAL_CONF)
        return user


    def get_key(self):
        """
        Is the key/password saved?
        """
        key = self.parser.get("credentials", "key", None)
        if key == "password_here":
            raise Exception("Key needs to be changed in %s" % LOCAL_CONF)
        return key

