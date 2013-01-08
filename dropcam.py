#!/usr/bin/env python
# ---------------------------------------------------------------------------------------------
# Copyright (c) 2012-2013, Ryan Galloway (ryan@rsgalloway.com)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# - Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# - Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# - Neither the name of the software nor the names of its contributors
# may be used to endorse or promote products derived from this software
# without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# ---------------------------------------------------------------------------------------------
# docs and latest version available for download at
# http://github.com/rsgalloway/dropcam
# ---------------------------------------------------------------------------------------------

import os
import sys
import urllib2
import cookielib
import simplejson as json
from urllib import urlencode

__doc__ = """
An unofficial Dropcam Python API.
"""

__author__ = "Ryan Galloway <ryan@rsgalloway.com>"

_NEXUS_BASE = "https://nexusapi.dropcam.com"
_API_BASE = "https://www.dropcam.com"
_API_PATH = "api/v1"
_LOGIN_PATH = "login.login"
_CAMERAS_PATH = "cameras.get_visible"
_IMAGE_PATH = "get_image"
_EVENT_PATH = "get_cuepoint"

class Dropcam(object):
    def __init__(self, username, password):
        """
        Creates a new dropcam API instance.

        :param username: Dropcam account username.
        :param password: Dropcam account password.
        """
        self.username = username
        self.password = password
        self.cookie = None
        self._login()

    def _request(self, path, params):
        base_url = "/".join([_API_BASE, _API_PATH, path])
        request_url = "?".join([base_url, urlencode(params)])
        request = urllib2.Request(request_url)
        if self.cookie:
            request.add_header('cookie', self.cookie)
        return urllib2.urlopen(request)

    def _login(self):
        params = dict(username=self.username, password=self.password)
        response = self._request(_LOGIN_PATH, params)
        self.cookie = response.headers.get('Set-Cookie')

    def cameras(self):
        """
        Returns a list of dropcam Camera objects attached to
        this account.
        """
        if not self.cookie:
            self._login()
        cameras = []
        params = dict(group_cameras=True)
        response = self._request(_CAMERAS_PATH, params)
        data = json.load(response)
        items = data.get('items')
        for item in items:
            params = item.get('owned')[0]
            params.update(cookie=self.cookie)
            cameras.append(Camera(params))
        return cameras

class Event(object):
    def __init__(self, params):
        """
        :param params: Dictionary of dropcam event attributes.
        """
        self.__dict__.update(params)

class Camera(object):
    def __init__(self, params):
        """
        :param params: Dictionary of dropcam camera attributes.
        """
        self.__dict__.update(params)
    
    def _request(self, path, params):
        base_url = "/".join([_NEXUS_BASE, path])
        request_url = "?".join([base_url, urlencode(params)])
        request = urllib2.Request(request_url)
        if self.cookie:
            request.add_header('cookie', self.cookie)
        return urllib2.urlopen(request)
    
    def events(self, start, end):
        """
        Returns a list of camera events for a given time period:

        :param start: start time in seconds since epoch
        :param end: end time in seconds since epoch
        """
        events = []
        params = dict(uuid=self.uuid, start_time=start, end_time=end, human=True)
        response = self._request(_EVENT_PATH, params)
        items = json.load(response)
        for item in items:
            events.append(Event(item))
        return events

    def get_image(self, width=720, time=None):
        """
        Requests a camera image, returns response object.
        
        :param width: image width or X resolution
        :param time: time of image capture (in seconds from ecoch)
        """
        params = dict(uuid=self.uuid, width=width)
        if time:
            params.update(time=time)
        return self._request(_IMAGE_PATH, params)

    def save_image(self, path, width=720, time=None):
        """
        Saves a camera image to disc. 

        :param path: file path to save image
        :param width: image width or X resolution
        :param time: time of image capture (in seconds from ecoch)
        """
        f = open(path, "wb")
        response = self.get_image(width, time)
        f.write(response.read())
        f.close()
