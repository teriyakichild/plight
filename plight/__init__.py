#!/usr/bin/env python

import cherrypy
import os

__version__ = '0.0.1'
__license__ = 'ASLv2'
__author__ = 'Josh Bell'
__author_email__ = 'josh.bell@rackspace.com'

CONFIG_FILE = '/etc/plight.conf'

class NodeStatus(object):
    def __init__(self, state_file, **kwargs):
        self.state_file = state_file
#        self._build_params(kwargs)
#
#    def _build_params(params):
#        for param, value in params.items():
#            setattr(self, param, value)

    # Operable Functions
    def set_node_disabled(self):
        open(self.state_file, 'a').close()
        current_status = 'DISABLED'
        return current_status

    def set_node_enabled(self):
        if os.path.exists(self.state_file): 
            try:
                os.remove(self.state_file)
                current_status = 'ENABLED'
            except OSError, e:
                #TODO: we dont do anything with this
                error = "Unable to enable node - Error: {} - {}.".format(e.filename, e.strerror)
        return self.get_node_status()

    def set_node_state(self, state):
        if state.lower() == 'enable':
            return self.set_node_enabled()
        elif state.lower() == 'disable':
            return self.set_node_disabled()
        raise Exception, 'Unknown state ({0}) requested'.format(state)

    def get_node_status(self):
        if os.path.isfile(self.state_file):
            current_status = 'DISABLED'
        else:
            current_status = 'ENABLED'
        return current_status
 
    # Web Server Operations
    @cherrypy.expose
    def index(self):
        return self.get_node_status()

    @cherrypy.expose
    def status(self):
        return "Node Status: " + self.get_node_status()
