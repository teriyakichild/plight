#!/usr/bin/env python

import cherrypy
import ConfigParser
import logging
import json as simplejson
import sys

Config=ConfigParser.ConfigParser()
Config.read("nodestatus.conf")

serverconfig = {'server.socket_host': Config.get('webserver', 'host'),
                'server.socket_port': Config.getint('webserver', 'port'),
                'log.screen': True
               }

log_location = Config.get('logging', 'logfile')

with open(log_location, 'a') as logfile:
    logfile.write('Starting NodeStatus Run\n')

class NodeStatus(object):
  
    state_file = Config.get('permanents', 'statefile')

    def write_node_status(self, state_file, status):
        with open(state_file, 'w') as statefile:
	    statefile.write(status)

    def read_node_status(self, state_file):
        with open(self.state_file, 'r') as statefile:
	    current_status=statefile.read()
	return current_status
 

    @cherrypy.expose
    def index(self):
        return "Node Status: " + self.read_node_status()

    @cherrypy.expose
    def status(self):
	current_status = self.read_node_status()
        return current_status

    @cherrypy.expose
    def enable(self):
        self.write_node_status('ENABLED')
	current_status = self.read_node_status()
        return current_status

    @cherrypy.expose
    def disable(self):
        self.write_node_status('DISABLED')
	current_status = self.read_node_status()
        return current_status

cherrypy.config.update(serverconfig)

cherrypy.quickstart(NodeStatus())
