#!/usr/bin/python
"""
Client library for the Lulu Publish API

Copyright 2010 Lulu Enterprises

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License. 
"""

import urllib2
import urllib
import simplejson
import os.path
import config as client_config
import exceptions
import traceback
import sys
import publish.common.project as cproject
import poster.encode as poster_encode
import poster.streaminghttp as poster_streaming


class Client:
    """
    Lulu Publication API interface.   Use this for writing your own applications
    that wish to publish things programatically on Lulu, or use this as a reference
    to develop your own API bindings in your favorite programming language, such as
    Haskell or Intercal.  Browsing the source code to lulu_publish (also a Python
    script) can show you how to build a complete and usable app and exercise
    the API functions.
    """

    def __init__(self, server=None, verbose=False):
        """
        Constructor.
        server:  the address/hostname of the lulu server, e.x. api1.lulu.com
        user:    username, ex: user@example.org
        key:     for now, the user's password
        """
        self.verbose = verbose
        self.config = client_config.Config()

        if server is None:
            self.server = self.config.get_publish_api_server()
        else:
            self.server = server

        self.token    = None  # login will fill this in
        self.user     = None  # " "
        # FIXME: use Python standard logging

    def login(self, user=None, key=None):
        """
        Login to the Lulu.com app and retrieve an auth_token that we will need
        for all future requests.
        """
        if user is None:
            user = self.config.get_user()
        if key is None:
            key = self.config.get_key()

        uri = "https://%s/account/endpoints/authenticator.php" % self.config.get_auth_server()
        post = {
           "username"     : user,
           "password"     : key,
           "responseType" : 'json'
        }

        post = urllib.urlencode(post)
        req = urllib2.Request(uri, post)
        try:
            handle = urllib2.urlopen(req)
        except urllib2.URLError, ue:
            print sys.stderr, "failure to contact %s" % uri
            traceback.print_exc()
        data = handle.read()
        try:
            data = simplejson.loads(data)
        except:
            print "Unable to parse response: %s" % data
            raise
        auth_ok = data.get("authenticated",False)
        if not auth_ok:
            # FIXME: use more custom exception types
            raise Exception("authentication failed")
        else:
            self.token = data.get("authToken",None)
            self.user  = user
            return self.token

    def create(self, project):
        """
        Create a new project.   Project is a publish.common.project.Project()
        """
        self.__assert_project(project, "project must be a publish.common.Project instance")
        ds = project.to_json()
        form_data = { "project" : ds }
        if self.verbose:
            print "creating with: ", ds
        return self.__submit("create",None,form_data)

    def update(self, project_or_dict):
        """
        Update an existing project.   Metadata is as described in create
        but may contain omissions as only changes are needed.
        Files is a list of files to upload and their context (FIXME).
        """
        self.__assert_valid_for_update(project_or_dict, "expected project or dictionary with content_id, recieved: %s" % project_or_dict)
        if type(project_or_dict) == type({}):
            ds = simplejson.dumps(project_or_dict)
        else:
            ds = project_or_dict.to_json()
        form_data = { "project" : ds  }
        if self.verbose:
            print "updating with: %s" % ds
        return self.__submit("update",None,form_data)

    def read(self, content_id, verbose=False):
        """
        Get the metadata about a given project.
        """
        self.__assert_positive_integer(content_id, "content id must be a positive integer")
        data = self.__submit("read", {"id": content_id}, None)
        if self.verbose:
            print "data read: ", simplejson.dumps(data, sort_keys=True, indent=4)
        assert type(data) == type({}), "expected the read call to return a dictionary: %s, got %s" % (data)
        assert data.has_key("project"), "expected the response to contain a project: %s" % data
        return cproject.Project(data["project"])

    def urls(self, content_id):
        """
        For a given project, return the 'contents' and 'cover' download
        URLs, as a hash:
        {
            'contents'  : 'http://...',
            'cover'     : 'http://...',
        }
        """
        self.__assert_positive_integer(content_id, "content id must be a positive integer")
        return self.__submit("urls", {"id": content_id}, None)

    def list_projects(self):
        """
        Get a list of content_ids suitable for use with the read or delete calls.
        """
        results = self.__submit("list", None, None)
        assert results.has_key("content_ids"), "content IDs were not returned"
        return results["content_ids"]

    def delete(self, content_id):
        """
        Delete a project, permanently, no questions asked.
        """
        self.__assert_positive_integer(content_id, "content id must be a positive integer")
        return self.__submit("delete", { "id" : content_id }, None)

    def download_file(self, content_id, what_file, save_as):
        """
        Download a print or preview output file for a given project.  This is usable for API consumer
        testing in an automated context.  To share URLs with users on your web site, use the urls() function
        and link to those directly.   Note that this implementation currently does *not* stream downloads,
        so if the document is expected to be very large, just use the urls() function.  The server itself
        does in fact stream downloads, so this is only a limitation of the client implementation.
        """
        self.__assert_positive_integer(content_id, "content id must be a positive integer")
        assert (what_file in ["contents", "cover"]), "file type must be 'contents' or 'cover'"
        self.__submit("download", { "id": content_id, "what": what_file }, download=save_as)
        if self.verbose:
            print "downloaded %s as %s" % (what_file, save_as)
        return save_as
  
    def upload(self, files):
        """
        Upload one or more files to the server.
        'files' is either a filename or an array of filenames.
        Upload must be called prior to creation.
        """
        assert self.token is not None, "call login(username, key) to obtain a token"
        assert self.user is not None, "internal error, no user value"
  
        poster_streaming.register_openers()
  
        # Start the multipart/form-data encoding of the files
        # headers contains the necessary Content-Type and Content-Length
        # datagen is a generator object that yields the encoded parameters
  
        input_hash = {}
        if type(files) == type(""):
            files = [ files ]
        for f in files:
            base = os.path.basename(f)
            input_hash[base] = open(f, "rb")
        input_hash["auth_token"] = self.token
        input_hash["auth_user"]  = self.user
        datagen, headers = poster_encode.multipart_encode(input_hash)
  
        # Create the Request object
  
        request = urllib2.Request("https://%s/api/publish/v1/upload" % self.server, datagen, headers)
  
        # Actually do the request, and get the response
        try:
            response = urllib2.urlopen(request).read()
        except urllib2.HTTPError, he:
            self.__convert_error_to_exception(he)
        print simplejson.loads(response)
        return simplejson.loads(response)

    def request_upload_token(self):
        """
        Request a token for use with file uploads.
        """
        return self.__submit("request_upload_token")

    def test_echo(self, parameters=None, form_data=None):
        """
        A simple echo method for unittest purposes.
        """
        assert type(parameters) == type({}) or parameters is None
        assert type(form_data) == type({}) or form_data is None
        return self.__submit("test_echo", parameters, form_data)

    def test_error1(self):
       """
       This method is here only for test purposes and can be used to
       cause a remote exception to simulate an expected failure, such
       as what would happen if input to a request was invalid.
       """
       return self.__submit("test_error1")
  
    def __submit(self, method, options=None, form_data=None, download=None):
        """
        Carries out a request to the REST endpoint
        "method" is, for example create/update/delete/read, etc
        "options" is a hash and is added to the URL line, ex: { "id" : 42 }
        "form_data" is a hash and is added to form data
        "download" if not None, means save the result to the filename provided
        """
        assert self.token is not None, "call login(username, key) first to obtain a token"
        assert self.user is not None, "internal error, no user value"
        assert method is not None, "method is required"
        uri = "https://%s/api/publish/v1/%s" % (self.server, method)
  
        # add object-addressible parameters to the URL line
        # in the example of __submit("read", { "id": 3 }) the URL end in /id/3
        if options is not None:
            for (k,v) in options.iteritems():
                uri = uri + "/%s/%s" % (k,v)
  
        # data to be posted includes all that the user wishes to post plus
        # the auth_user and auth_token obtained from the login call
        if form_data is None:
            form_data = {}
        form_data["auth_token"] = self.token
        form_data["auth_user"]  = self.user
        form_data = urllib.urlencode(form_data)
  
        req = urllib2.Request(uri, form_data)
  
        # by default, return the JSON value we get back from the server
        # unless a download location is specified 
        if download is None:
            try:
                handle = urllib2.urlopen(req)
                data = handle.read()
            except urllib2.HTTPError, he:
                self.__convert_error_to_exception(he)
            try:
                return simplejson.loads(data)
            except:
                raise Exception("invalid JSON data returned from server: <<%s>>" % data)
        else:
            try:
                handle = urllib2.urlopen(req)
            except urllib2.HTTPError, he:
                self.__convert_error_to_exception(he)
            fd = open(download, "w")
            while True:
                data = handle.read(4092)
                if data == "":
                    break
                fd.write(data)
            fd.close()
            return download
  
    def __convert_error_to_exception(self, error):
        """
        Given a remote exception, return a client exception that makes it appear local.
        The server may have returned formatted data about the reason behind the remote
        error that we wish to pass to the client.
        """
        if error.code == 500:
            # internal server error -- something went wrong remotely.
            # we should have JSON data in the output, so reconstruct a local exception
            data = error.read()
            try:
                data = simplejson.loads(data)
            except:
                # error data returned was not JSON, just raise a generic exception
                raise Exception("Unexpected remote error: %s" % data)
            # add the error code into the packet and create the local exception 
            data["HTTPErrorCode"] = error.code
            data = simplejson.dumps(data)
            raise ClientException(data)
        else:
            # if it is not an internal server error, (i.e. HTTP_UNAUTHORIZED, etc)
            # just re-raise the error, it is sufficiently detailed
            raise
  
    def __assert_positive_integer(self, x, msg):
        """
        Validate that x is a positive integer
        """
        assert ((type(x) == int) and x > 0), msg
  
    def __assert_project(self, x, msg):
        """
        Validate that x is a publish.common.Project
        """
        assert (isinstance(x,cproject.Project)), msg
  
    def __assert_valid_for_update(self, project_or_dict, msg):
        """
        Validate that x is either a publish.common.Project or a hash
        that contains a content_id, meaning it is most likely suitable
        for sending to the update call as a partial delta update (see update docs)
        """
        if type(project_or_dict) == type({}):
            assert project_or_dict.has_key("content_id"), msg
        else:
            assert isinstance(project_or_dict, cproject.Project), msg


class ClientException(exceptions.Exception):
    """
    Custom exception for tracking of fatal errors.   This is here
    to simply the life of the client library and code that uses it,
    such that remote exception details can easily be read as opposed
    to just getting "error 500" (ISE) and so forth.
    """

    def __init__(self,value):
        """
        Constructed like any other exception, except the value here is going
        to be a string in JSON format. 
        """
        self.value = value 
        self.payload = self.get_json_exception_payload()
        self.from_koan = 1

    def __str__(self):
        """
        If printed, just print out the JSON blob.
        """
        return repr(self.value)

    def get_json_exception_payload(self):
        """
        Convert the input JSON to a string, and die with another exception
        if the server returned malformed results.
        """
        try:
            return simplejson.loads(self.value)
        except Exception, e:
            traceback.print_exc()
            raise Exception("Failed to extract details behind remote error: %s" % self.value)

    def get_exception_type(self):
        """
        What was the type of the remote exception?  ex: ApiException, KaboomException, etc
        """
        return self.payload.get("error_type","unknown") 

    def get_exception_value(self):
        """
        What string was the remote exception raised with?   Note that remote tracebacks
        are *not* provided, though this will explain the cause of the actual error.  If
        needed, Lulu will have server side logs.
        """
        return self.payload.get("error_value","unknown")
