#!/usr/bin/env python

from __future__ import print_function

import os
import pwd
import grp
import sys
import time
import signal
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
import plight.config as plconfig

PID = PIDLockFile(plconfig.PID_FILE)


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
        applogging_handler = RotatingFileHandler(
            config['log_file'],
            mode='a',
            maxBytes=config['log_filesize'],
            backupCount=config['log_rotation_count'])
        applogger.addHandler(applogging_handler)

    # if pidfile is locked, do not start another process
    if PID.is_locked():
        sys.stderr.write('Plight is already running\n')
        sys.exit(1)

    context = DaemonContext(pidfile=PID,
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
    if PID.is_locked():
        pid = PID.read_pid()
        os.kill(int(pid), signal.SIGTERM)
    else:
        print('no pid file available')


def format_get_current_state(state, details):
    warning = ''
    if not PID.is_locked():
        warning = 'WARNING: plight is not running\n'
    message = '{0}State: {1}\nCode: {2}\nMessage: {3}\n'
    sys.stdout.write(
        message.format(warning, state, details['code'], details['message']))


def format_list_states(default, states):
    for state, details in states.items():
        message_modifier = ''
        if state == default:
            message_modifier = ' [default]'
        message = 'State: {0}{1}\nCode: {2}\nMessage: {3}\n\n'
        sys.stdout.write(
            message.format(
                state, message_modifier, details['code'], details['message']))


def cli_fail(commands):
    fail_msg = '{0} [start|{1}|list-states|status|stop]\n'
    commands = "|".join(commands)
    sys.stderr.write(fail_msg.format(sys.argv[0], commands))
    exit(1)


def run():
    config = plconfig.get_config()
    node = plight.NodeStatus(states=config['states'])

    try:
        mode = sys.argv[1].lower()
    except IndexError:
        cli_fail(node._commands)
    except AttributeError:
        cli_fail(node._commands)
    if mode in node._commands:
        log_message('Changing state to {0}'.format(mode))
        node.set_node_state(mode)
    elif mode == 'start':
        start_server(config)
    elif mode == 'status':
        format_get_current_state(node.state, config['states'][node.state])
    elif mode == 'list-states':
        format_list_states(node._default_state, config['states'])
    elif mode == 'stop':
        stop_server()
    else:
        cli_fail(node._commands)
