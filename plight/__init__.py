#!/usr/bin/env python
"""Plight, daemon to report the status of a node

"""

__version__ = '0.0.4'
__license__ = 'ASLv2'
__all__ = ['StatusHTTPRequestHandler', 'NodeStatus']
__author__ = 'Alex Schultz'
__author_email__ = 'Alex.Schultz@rackspace.com'

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import BaseHTTPServer
import SimpleHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

STATE_FILE = '/var/tmp/node_disabled'
CONFIG_FILE = '/etc/plight.conf'

class StatusHTTPRequestHandler(SimpleHTTPRequestHandler,object):
    """Status HTTP Request handler

    This is a class to handle a status request.  Only GET/HEAD requests are valid. 
    The handler will return 200 if the node is OK, and a 404 is the node is unavailable.
    If any 50x errors are returned, either the request is bad or the NodeStatus
    object may be misconfigured.
    """


    server_version = 'StatusServer'

    _weblogger = None
    _applogger = None
    _node_status = None

    def get_node_status(self):
        """Get node status object

        This will return the NodeStatus object for this object
        """
        if self._node_status is None:
            self._node_status = NodeStatus()
        return self._node_status

    def get_web_logger(self):
        """Get web logger
        The function will get a logger named plight_httpd for web logs
        """
        if self._weblogger is None:
           self._weblogger = logging.getLogger('plight_httpd')
        return self._weblogger

    def get_app_logger(self):
        """Get app logger
        The function will get a logger named plight for app logs
        """
        if self._applogger is None:
           self._applogger = logging.getLogger('plight')
        return self._applogger


    def version_string(self):
        """Return the version (override)

        This overrides the default version string to remove the version numbers
        """
        return self.server_version

    def do_GET(self):
        """Handle GET requests

        This returns the status of the node based on what the NodeStatus object
        returns.
        """
        status = self.get_node_status()

        if status is None:
            self.send_error(code=500,message='node_status unavailable')
        else:
            if status.get_node_state() is 'ENABLED':
                self.send_response(code=200)
            else:
                self.send_error(code=404,message='node is unavailable')

    def do_HEAD(self):
      """Handle HEAD requests

      This returns the status of the node based on what the NodeStatus object
      returns, but not in an unnecessarily verbose way.
      """
      self.do_GET()

    def log_request(self, code='-', size='-'):
        """Log the request (override)

        Create a request log entry for the request.
        """
        self.get_web_logger().info('%s - - [%s] "%s" %s %s' %
            (self.address_string(),
            self.log_date_time_string(),
            self.requestline,
            str(code),
            str(size)))

    def log_message(self, format, *args):
        """Log message override

        Overrides the default log_message function to do nothing
        """
        self.get_app_logger().info("%s - - [%s] %s\n" %
            (self.address_string(),
             self.log_date_time_string(),
             format%args))

class _Singleton(type):
    """Singleton class

    Pulled from http://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
    """
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Singleton(_Singleton('SingletonMeta', (object,), {})):
    pass

class NodeStatus(Singleton):
    """NodeStatus class

    This class checks for the existance of a file indicating the node should
    be unavailable.
    """
    _applogger = None

    def __init__(self, state_file=STATE_FILE):
        self._applogger = logging.getLogger('plight')
        self.state_file = state_file

    def set_state_file(self, state_file=STATE_FILE):
        self.state_file = state_file

    def get_app_logger(self):
        """Get app logger
        The function will get a logger named plight for app logs
        """
        if self._applogger is None:
           self._applogger = logging.getLogger('plight')
        return self._applogger

    # Operable Functions
    def set_node_disabled(self):
        """Set the node disabled

        This will create a state file to be used to indicate the node
        is unavailable.
        """
        open(self.state_file, 'a').close()

    def set_node_enabled(self):
        """Set the node enabled

        This will attempt to remove a state file if one exists and
        the node will now return that it is enabled.
        """
        if os.path.exists(self.state_file):
            try:
                os.remove(self.state_file)
            except OSError, e:
                #TODO: we dont do anything with this
                error = "Unable to enable node - Error: {} - {}.".format(e.filename, e.strerror)
        return self.get_node_state()

    def set_node_state(self, state):
        """Set node state

        This can be used to toggle the state of the node
        """
        if state.lower() == 'enable':
            return self.set_node_enabled()
        elif state.lower() == 'disable':
            return self.set_node_disabled()
        raise Exception, 'Unknown state ({0}) requested'.format(state)

    def get_node_state(self):
        """Get the node state

        Check if the state file exists indicating the node is disabled.
        If the file is missing, the node is enabled.
        """
        if os.path.isfile(self.state_file):
            current_status = 'DISABLED'
        else:
            current_status = 'ENABLED'
        return current_status

def test(HandlerClass = StatusHTTPRequestHandler,
         ServerClass = BaseHTTPServer.HTTPServer):
    SimpleHTTPServer.test(HandlerClass, ServerClass)

if __name__ == '__main__':
    test()
