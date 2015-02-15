#!/usr/bin/env python
# ---------------------------------------------------------------------------------------------
# Copyright (c) 2012-2015, Ryan Galloway (ryan@rsgalloway.com)
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
import time
import logging
import urllib2
import cookielib
from urllib import urlencode
try:
    import simplejson as json
except ImportError:
    import json

__doc__ = """
Unofficial Dropcam Python API.
"""

__author__ = "Ryan Galloway <ryan@rsgalloway.com>"
__version__ = "0.3.2"

logging.basicConfig()
log = logging.getLogger("dropcam")

class ConnectionError(IOError):
    """
    Exception used to indicate issues with connectivity or HTTP
    requests/responses
    """

def _request(path, params, cookie=None):
    """
    Dropcam http request function.
    """
    request_url = "?".join([path, urlencode(params)])
    request = urllib2.Request(request_url)
    if cookie:
        request.add_header('cookie', cookie)
    try:
        return urllib2.urlopen(request)
    except urllib2.HTTPError:
        log.error("Bad URL: %s" % request_url)
        raise

def _request_post(request_url, data, cookie, uuid=None):
    """
    Dropcam http post request function.
    """

    clen = len(str(data))
    data = urlencode(data)
    req = urllib2.Request(request_url)

    if uuid:
        req.add_header('Referer', "/".join([Dropcam.API_BASE, 'watch', uuid]))
    else:
        req.add_header('Referer', Dropcam.API_BASE)

    if cookie:
        req.add_header('Content-Type', 'application/json')
        req.add_header('Content-Length', clen)
        req.add_header('cookie', cookie)

    try:
        return urllib2.urlopen(req, data=data)
    except urllib2.HTTPError:
        log.error("Bad URL: %s" % request_url)
        raise

class Dropcam(object):

    NEXUS_BASE = "https://nexusapi.dropcam.com"
    API_BASE = "https://www.dropcam.com"
    API_PATH = "api/v1"

    LOGIN_PATH =  "/".join([API_BASE, API_PATH, "login.login"])
    CAMERAS_GET =  "/".join([API_BASE, API_PATH, "cameras.get"])
    CAMERAS_UPDATE =  "/".join([API_BASE, API_PATH, "cameras.update"])
    CAMERAS_GET_VISIBLE =  "/".join([API_BASE, API_PATH, "cameras.get_visible"])
    CAMERAS_GET_IMAGE_PATH = "/".join([NEXUS_BASE, "get_image"])
    EVENT_PATH =  "/".join([NEXUS_BASE, "get_cuepoint"])
    EVENT_GET_CLIP_PATH = "/".join([NEXUS_BASE, "get_event_clip"])
    PROPERTIES_PATH = "/".join([API_BASE, "app/cameras/properties"])

    def __init__(self, username, password):
        """
        Creates a new dropcam API instance.

        :param username: Dropcam account username.
        :param password: Dropcam account password.
        """
        self.__username = username
        self.__password = password
        self.cookie = None
        self._login()

    def _login(self):
        params = dict(username=self.__username, password=self.__password)
        response = _request_post(self.LOGIN_PATH, params, cookie=None)
        data = json.load(response)

        # dropcam returns 200 even when it's an auth fail.
        # Still checking both to be proper.
        if response.getcode() not in (200, 201) or data.get('status') not in (0, 200, 201):
            print("login failed and returned status code %s. login json: %s"
                % (response.getcode(), json.dumps(data)))
            raise Exception
        cookie = response.headers.get('Set-Cookie')
        self.cookie = cookie.split(';')[0]  # Only return the 'website_2' Cookie.

    def cameras(self):
        """
        :returns: list of Camera class objects
        """
        if not self.cookie:
            self._login()
        cameras = []
        params = dict(group_cameras=True)
        response = _request(self.CAMERAS_GET_VISIBLE, params, self.cookie)
        data = json.load(response)
        items = data.get('items')
        for item in items:
            for params in item.get('owned'):
                cameras.append(Camera(self, params))
        return cameras

class Event(object):
    def __init__(self, camera, params):
        """
        :param params: Dictionary of dropcam event attributes.
        """
        self.camera = camera
        self.__dict__.update(params)

class Camera(object):
    def __init__(self, dropcam, params):
        """
        :param params: Dictionary of dropcam camera attributes.
        :returns: addinfourl file-like object
        :raises: urllib2.HTTPError, urllib2.URLError
        """
        self.dropcam = dropcam
        self.__dict__.update(params)

    def __repr__(self):
        return "<dropcam.Camera '%s'>" % self.title

    def set_property(self, name, value):
        """
        Changes a property on the camera

        :param name: the name of the property to change
        :param value: the value to change the property to

        Examples:
            irled.state: auto_on / always_on / always_off
            streaming.enabled: true / false
            streaming.params.hd: true / false
            audio.enabled: true / false
            statusled.enabled: true / false
        """
        url = "/".join([Dropcam.PROPERTIES_PATH, self.uuid])

        data = {
            'camera_uuid':self.uuid, 
            'name':name, 
            'value':value
        }

        resp = _request_post(url, data, self.dropcam.cookie, self.uuid)

        if not resp.getcode() in (200, ):
            log.error("Error setting property: %s" % resp.msg)

    def events(self, start, end=None):
        """
        Returns a list of camera events for a given time period:

        :param start: start time in seconds since epoch
        :param end: end time in seconds since epoch (defaults to current time)
        :returns: list of Event class objects
        """
        start = int(start)
        if end is None:
            end = int(time.time())
        events = []
        params = dict(uuid=self.uuid, start_time=start, end_time=end)
        response = _request(Dropcam.EVENT_PATH, params, self.dropcam.cookie)
        items = json.load(response)
        for item in items:
            events.append(Event(self, item))
        return events

    def get_image(self, width=720, seconds=None):
        """
        Requests a camera image, returns response object.
        
        :param width: image width or X resolution
        :param seconds: time of image capture (in seconds from epoch)
        :returns: response object
        :raises: ConnectionError
        """
        params = dict(uuid=self.uuid, width=width)
        if seconds:
            params.update(time=seconds)
        response = _request(Dropcam.CAMERAS_GET_IMAGE_PATH, params, self.dropcam.cookie)

        if (
            response.code != 200
            or not int(response.headers.getheader('content-length', 0))
        ):
            # Either a connection error or empty image sent with code 200
            raise ConnectionError(
                'Camera image is not available or camera is turned off',
            )

        return response

    def save_image(self, path, width=720, seconds=None):
        """
        Saves a camera image to disc. 

        :param path: file path to save image
        :param width: image width or X resolution
        :param seconds: time of image capture (in seconds from epoch)
        :raises: ConnectionError
        """
        f = open(path, "wb")
        response = self.get_image(width, seconds)
        f.write(response.read())
        f.close()

if __name__ == "__main__":
    d = Dropcam(os.getenv("DROPCAM_USERNAME"), 
                os.getenv("DROPCAM_PASSWORD"))
    try:
        for i, cam in enumerate(d.cameras()):
            print "saving image on", cam.title
            cam.save_image("dropcam.%d.jpg" % i)
            s = int(time.time() - (60 * 60 * 24 * 7))
            print cam.events(s)
    except Exception, err:
        print err
