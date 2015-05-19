#!/usr/bin/env python
"""Plight, daemon to report the status of a node

"""

__version__ = '0.1.1'
__license__ = 'ASLv2'
__all__ = ['StatusHTTPRequestHandler', 'NodeStatus']
__author__ = 'Alex Schultz'
__author_email__ = 'Alex.Schultz@rackspace.com'

import os
import logging
import time
try:
    import BaseHTTPServer
    from SimpleHTTPServer import test as http_server_test
    from SimpleHTTPServer import SimpleHTTPRequestHandler
except ImportError:
    import http.server as BaseHTTPServer
    from http.server import test as http_server_test
    from http.server import SimpleHTTPRequestHandler

STATES = {
    'enabled': {
        'command': 'enable',
        'file': None,
        'code': 200,
        'message': 'OK',
        'priority': 0
    },
    'disabled': {
        'command': 'disable',
        'file': '/var/tmp/node_disabled',
        'code': 404,
        'message': 'node is unavailable',
        'priority': 1
    },
    'offline': {
        'file': '/var/tmp/node_offline',
        'code': 503,
        'message': 'node is offline',
        'priority': 2
    },
}
CONFIG_FILE = '/etc/plight.conf'


class StatusHTTPRequestHandler(SimpleHTTPRequestHandler, object):

    """Status HTTP Request handler

    This is a class to handle a status request.
    Only GET/HEAD requests are valid.

    All valid responses from this handler will now come from
    the state configuration.

    If a 500 error is returned, either the request
    is bad or the NodeStatus object may be misconfigured.
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
            self.send_error(code=500, message='node_status is unavailable')
        else:
            status.get_node_state()
            code = status.get_state_detail('code')
            message = status.get_state_detail('message')
            self.send_response(code, message)

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
                                    format % args))


class _Singleton(type):

    """Singleton class

    Pulled from:
    http://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                _Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Singleton(_Singleton('SingletonMeta', (object,), {})):
    pass


class NodeStatus(Singleton):

    """NodeStatus class

    This class checks for the existance of a file indicating the node should
    be unavailable.
    """
    _applogger = None
    _default_state = None

    def __init__(self, states=STATES):
        self._applogger = logging.getLogger('plight')
        self.states = states
        self._commands = {}
        for (state, state_data) in self.states.items():
            if state_data['file'] is None:
                if getattr(self, '_default_state') is not None:
                    raise Exception('More than 1 state with undefined file')
                self._default_state = state
            self._commands[state_data.get('command', state)] = state
        if self._default_state is None:
            raise Exception('No default state defined')
        self.get_node_state()

    def set_state_file(self, state, state_file):
        self.states[state]['file'] = state_file

    def get_app_logger(self):
        """Get app logger
        The function will get a logger named plight for app logs
        """
        if self._applogger is None:
            self._applogger = logging.getLogger('plight')
        return self._applogger

    # Operable Functions
    def _clear_state_files(self):
        """Clear out all the active state files, resetting to default state"""
        for (state, state_data) in self.states.items():
            if state_data['file'] is None:
                continue
            if os.path.exists(state_data['file']):
                try:
                    os.remove(state_data['file'])
                except OSError as e:
                    err = "Unable to clear {} state - Error: {} - {}.".format(
                        state, e.filename, e.strerror)
                    self._applogger.error("{} {}".format(
                        time.strftime('%c'), err))

    def set_node_offline(self):
        """Set the node offline

        This will create a state file to be used to indicate the node
        is purposefully offline.
        """
        return self.set_node_state('offline')

    def set_node_disabled(self):
        """Set the node disabled

        This will create a state file to be used to indicate the node
        is unavailable, primarily for maintainance mode behaviors.
        """
        return self.set_node_state('disable')

    def set_node_enabled(self):
        """Set the node enabled

        This will attempt to remove a state file if one exists and
        the node will now return that it is enabled.
        """
        return self.set_node_state('enable')

    def set_node_state(self, state):
        """Set node state

        This can be used to toggle the state of the node
        """
        state = state.lower()
        if state not in self.states:
            if state in self._commands:
                state = self._commands[state]
            else:
                raise Exception('Unknown state ({0}) requested'.format(state))
        self._clear_state_files()
        if self.states[state]['file'] is not None:
            open(self.states[state]['file'], 'a').close()
        return self.get_node_state()

    def get_node_state(self):
        """Get the node state

        Check if the state file exists indicating the node is disabled.
        If the file is missing, the node is enabled.
        """
        active_states = {}
        current_state = self._default_state
        for (state, state_data) in self.states.items():
            value = check_state(state_data['file'])
            active_states[state] = value
            if value and compare_priority(self.states, current_state, state):
                current_state = state
        if current_state == self._default_state:
            active_states[current_state] = not any(active_states.values())
        self.state = current_state
        return current_state.upper()

    def get_state_detail(self, detail, state=None):
        if state is None:
            if self.state is None:
                self.get_node_state()
            state = self.state
        return self.states[state][detail]

def compare_priority(states, state1, state2):
    return states[state1]['priority'] < states[state2]['priority']


def check_state(state_file):
    if state_file is None:
        return None
    return os.path.isfile(state_file)


def test(HandlerClass=StatusHTTPRequestHandler,
         ServerClass=BaseHTTPServer.HTTPServer):
    http_server_test(HandlerClass, ServerClass)


if __name__ == '__main__':
    test()
