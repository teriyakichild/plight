#!/usr/bin/env python

import os
import sys
import signal
import ConfigParser
import BaseHTTPServer
import SimpleHTTPServer
from daemon import DaemonContext
from daemon.pidlockfile import PIDLockFile
import logging
from logging.handlers import RotatingFileHandler
import plight

PID_FILE = '/var/run/plight.pid'

def get_config(config_file=plight.CONFIG_FILE):
    config = ConfigParser.ConfigParser()
    config.read(config_file)
    return {
           'host': config.get('webserver', 'host'),
           'port': config.getint('webserver', 'port'),
           'state_file': config.get('permanents', 'statefile'),
           'log_file': config.get('logging', 'logfile'),
           'log_level': config.get('logging', 'loglevel'),
           'log_filesize': config.getint('logging', 'filesize'),
           'log_rotation_count': config.getint('logging', 'rotationcount')
    }

def start_server(config):
    pidfile = PIDLockFile(PID_FILE)
    context = DaemonContext(pidfile=pidfile)
    context.open()
    try:
        logger = logging.getLogger('httpd')
        logger.setLevel(config['log_level'])
        if logger.handlers == []:
            logging_handler = RotatingFileHandler(config['log_file'],
                                                  mode='a',
                                                  maxBytes=config['log_filesize'],
                                                  backupCount=config['log_rotation_count'])
            logger.addHandler(logging_handler)

        node_status = plight.NodeStatus(config['state_file'])
        server_class = BaseHTTPServer.HTTPServer
        http = server_class((config['host'],
                             config['port']),
                             plight.StatusHTTPRequestHandler)
        http.serve_forever()
    finally:
        context.close()

def stop_server():
    if os.path.isfile(PID_FILE):
        fp = open(PID_FILE, 'r')
        pid = fp.read()
        fp.close()
        os.kill(int(pid), signal.SIGTERM)
    else:
        print "no pid file available"

def cli_fail():
    sys.stderr.write('{0} [start|enable|disable|stop]'.format(sys.argv[0]))

def run():
    try:
        mode = sys.argv[1].lower()
    except IndexError:
        cli_fail()
    except AttributeError:
        cli_fail()

    config = get_config()

    if mode.lower() in ['enable','disable']:
        node = plight.NodeStatus(state_file=config['state_file'])
        node.set_node_state(mode)
    elif mode.lower() == 'start':
        start_server(config)
    elif mode.lower() == 'stop':
        stop_server()
    else:
        cli_fail()
