#!/usr/bin/env python

import cherrypy
import ConfigParser
import sys
import plight
import daemon
import daemon.pidlockfile 
import signal

def get_config(config_file):
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
	cherrypy.config.update(config)
	cherrypy.quickstart(NodeStatus())
    signal.signal(signal.SIGTERM, stop_server)
    signal.signal(signal.SIGKILL, stop_server)
    create_lock_file()

def stop_server(signum, stack):
    cherrypy.engine.exit()
    remove_lock_file()
    sys.exit()

def create_lock_file():
    pidfile = daemon.pidlockfile.PIDLockFile("/var/run/zebra.pid")
    with daemon.DaemonContext(pidfile=pidfile):
        check = Node()
        check.run()

def remove_lock_file():
    #TODO so umm.. ya ?
    return    

def cli_fail():
    sys.stderr.write('{0} [start|enable|disable]'.format(sys.argv[0]))

def run():
    try:
        mode = sys.argv[1].lower()
    except IndexError:
        cli_fail()
    except AttributeError:
        cli_fail()
    config = get_config(plight.CONFIG_FILE)
    server_config = get_server_config(config)
    if mode.lower() in ['enable','disable']:
        node = NodeStatus()
        node.set_node_state(mode)
    elif node.lower() == 'start':
        start_server(config)
    else:
        cli_fail()