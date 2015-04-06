#!/usr/bin/env python

from __future__ import print_function

import os
import pwd
import grp
import sys
import time
import signal
try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser
try:
    import BaseHTTPServer
except ImportError:
    import http.server as BaseHTTPServer
from daemon import DaemonContext
try:
    from daemon.pidlockfile import PIDLockFile
except ImportError:
    from daemon.pidfile import PIDLockFile
import logging
from logging.handlers import RotatingFileHandler
import plight

PID_FILE = '/var/run/plight/plight.pid'


def get_config(config_file=plight.CONFIG_FILE):
    config = ConfigParser.ConfigParser()
    config.read(config_file)
    return {
        'host': config.get('webserver', 'host'),
        'port': config.getint('webserver', 'port'),
        'user': config.get('webserver', 'user'),
        'group': config.get('webserver', 'group'),
        'web_log_file': config.get('webserver', 'logfile'),
        'web_log_level': getattr(logging,
                                 config.get('webserver', 'loglevel')),
        'web_log_filesize': config.getint('webserver', 'filesize'),
        'web_log_rotation_count': config.getint('webserver', 'rotationcount'),
        'state_file': config.get('permanents', 'statefile'),
        'log_file': config.get('logging', 'logfile'),
        'log_level': getattr(logging,
                             config.get('logging', 'loglevel')),
        'log_filesize': config.getint('logging', 'filesize'),
        'log_rotation_count': config.getint('logging', 'rotationcount')
    }


def start_server(config):
    weblogger = logging.getLogger('plight_httpd')
    weblogger.setLevel(config['web_log_level'])
    if weblogger.handlers == []:
        weblogging_handler = RotatingFileHandler(config['web_log_file'],
                                                 mode='a',
                                                 maxBytes=config[
                                                     'web_log_filesize'],
                                                 backupCount=config[
                                                     'web_log_rotation_count'])
        weblogger.addHandler(weblogging_handler)

    applogger = logging.getLogger('plight')
    applogger.setLevel(config['log_level'])
    if applogger.handlers == []:
        applogging_handler = RotatingFileHandler(config['log_file'],
                                                 mode='a',
                                                 maxBytes=config[
                                                      'log_filesize'],
                                                 backupCount=config[
                                                      'log_rotation_count'])
        applogger.addHandler(applogging_handler)

    pidfile = PIDLockFile(PID_FILE)
    context = DaemonContext(pidfile=pidfile,
                            uid=pwd.getpwnam(config['user']).pw_uid,
                            gid=grp.getgrnam(config['group']).gr_gid,
                            files_preserve=[
                                weblogging_handler.stream,
                                applogging_handler.stream,
                            ],)
    context.stdout = applogging_handler.stream
    context.stderr = applogging_handler.stream
    context.open()
    os.umask(0o022)

    try:
        try:
            log_message('Plight is starting...')
            node_status = plight.NodeStatus(config['state_file'])
            server_class = BaseHTTPServer.HTTPServer
            http = server_class((config['host'],
                                 config['port']),
                                plight.StatusHTTPRequestHandler)
            http.serve_forever()
        except SystemExit as sysexit:
            log_message("Stopping... " + str(sysexit))
        except Exception as ex:
            log_message("ERROR: " + str(ex))
    finally:
        log_message('Plight has stopped...')
        context.close()


def log_message(message):
    applogger = logging.getLogger('plight')
    applogger.info("%s %s" %
                   (time.strftime('%c'),
                    message))


def stop_server():
    if os.path.isfile(PID_FILE):
        fp = open(PID_FILE, 'r')
        pid = fp.read()
        fp.close()
        os.kill(int(pid), signal.SIGTERM)
    else:
        print('no pid file available')


def cli_fail():
    sys.stderr.write('{0} [start|enable|disable|stop]\n'.format(sys.argv[0]))
    exit(1)


def run():
    try:
        mode = sys.argv[1].lower()
    except IndexError:
        cli_fail()
    except AttributeError:
        cli_fail()

    config = get_config()

    if mode.lower() in ['enable', 'disable']:
        node = plight.NodeStatus(state_file=config['state_file'])
        node.set_node_state(mode)
    elif mode.lower() == 'start':
        start_server(config)
    elif mode.lower() == 'stop':
        stop_server()
    else:
        cli_fail()
