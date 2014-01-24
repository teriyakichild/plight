#!/usr/bin/env python

import cherrypy
from cherrypy.process.plugins import PIDFile
from cherrypy.process.plugins import Daemonizer

import ConfigParser
import sys
import plight
import signal
import os

PID_FILE = '/var/run/plight.pid'

def get_config(config_file=plight.CONFIG_FILE):
    config = ConfigParser.ConfigParser()
    config.read(config_file)
    return {
           'host': config.get('webserver', 'host'),
           'port': config.getint('webserver', 'port'),
           'state_file': config.get('permanents', 'statefile'),
           'log_file': config.get('logging', 'logfile'),
           'log_level': config.get('logging', 'loglevel')
    }

def get_server_config(config=None):
    if config is None:
        config = get_config()
    return {
            'server.socket_host': config['host'],
            'server.socket_port': config['port'],
            'log.screen': True
    }

def _daemonize():
    Daemonizer(cherrypy.engine).subscribe()
    PIDFile(cherrypy.engine, PID_FILE).subscribe()

def start_server(config, server_config):
    _daemonize()
    cherrypy.config.update(server_config)
    cherrypy.quickstart(plight.NodeStatus(state_file=config['state_file']))
    signal.signal(signal.SIGTERM, _shutdown_server)
    signal.signal(signal.SIGKILL, _shutdown_server)

def _shutdownp_server(signum, stack):
    cherrypy.engine.exit()
    sys.exit()

def stop_server():
    if os.path.isfile(PID_FILE):
        fp = open(PID_FILE, 'r')
        pid = fp.read()
        fp.close()
        os.kill(int(pid), signal.SIGTERM)
    else:
        print "no pid file available"

def cli_fail():
    sys.stderr.write('{0} [start|enable|disable]'.format(sys.argv[0]))

def run():
    try:
        mode = sys.argv[1].lower()
    except IndexError:
        cli_fail()
    except AttributeError:
        cli_fail()
    config = get_config()
    server_config = get_server_config(config)
    if mode.lower() in ['enable','disable']:
        node = plight.NodeStatus(state_file=config['state_file'])
        node.set_node_state(mode)
    elif mode.lower() == 'start':
        start_server(config, server_config)
    elif mode.lower() == 'stop':
        stop_server()
    else:
        cli_fail()
