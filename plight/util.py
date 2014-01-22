#!/usr/bin/env python

import cherrypy
from cherrypy.process.plugins import PIDFile
from cherrypy.process.plugins import Daemonizer

import ConfigParser
import sys
import plight
import daemon
import daemon.pidlockfile 
import signal

PID_FILE = '/var/run/plight.pid'

def get_config(config_file=plight.CONFIG_FILE):
    config = ConfigParser.ConfigParser()
    config.read(config_file)
    return config

def get_server_config(config):
    return {
            'server.socket_host': config.get('webserver', 'host'),
            'server.socket_port': config.getint('webserver', 'port'),
            'log.screen': True
    }

def start_server(config):
    Daemonizer(cherrypy.engine).subscribe()
    cherrypy.config.update(config)
    cherrypy.quickstart(NodeStatus())
    signal.signal(signal.SIGTERM, stop_server)
    signal.signal(signal.SIGKILL, stop_server)
    create_lock_file()

def stop_server(signum, stack):
    cherrypy.engine.exit()
    sys.exit()

def create_lock_file(lock_file=PID_FILE):
    PIDFile(cherrypy.engine, lock_file).subscribe()

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
        node = NodeStatus()
        node.set_node_state(mode)
    elif node.lower() == 'start':
        start_server(config)
    else:
        cli_fail()
