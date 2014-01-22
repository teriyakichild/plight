#!/usr/bin/env python

import cherrypy
import ConfigParser
import logging
import json as simplejson
import os

# Get Configuration
config_file = "nodestatus.conf"
Config=ConfigParser.ConfigParser()
Config.read(config_file)

# Config Web Server
serverconfig = {'server.socket_host': Config.get('webserver', 'host'),
                'server.socket_port': Config.getint('webserver', 'port'),
                'log.screen': True
               }

# Improve Logging
log_location = Config.get('logging', 'logfile')

with open(log_location, 'a') as logfile:
    logfile.write('Starting NodeStatus Run\n')

# Initialize Web Server Class
class NodeStatus(object):
  
    state_file = Config.get('permanents', 'statefile')
 
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
	        error = "Unable to enable node - Error: {} - {}.".format(e.filename, e.strerror)
	current_status = self.get_node_status()
	return current_status

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

    @cherrypy.expose
    def enable(self):
        return self.set_node_enabled()

    @cherrypy.expose
    def disable(self):
        return self.set_node_disabled()

# Update Web Server Config
cherrypy.config.update(serverconfig)

# Start Web Server
cherrypy.quickstart(NodeStatus())
