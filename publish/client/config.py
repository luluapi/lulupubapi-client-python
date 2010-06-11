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


Copyright 2010 Lulu Enterprises

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License. 
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
api_key = api_key_here
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

    def get_upload_server(self):
        """
        Where is the PHP authentication endpoint?
        """
        return self.parser.get("server", "upload_server", "127.0.0.1")

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

    def get_api_key(self):
        """
        Is the api key saved?
        """
        key = self.parser.get("credentials", "api_key", None)
        if key == "api_key_here":
            raise Exception("API key needs to be changed in %s" % LOCAL_CONF)
        return key

