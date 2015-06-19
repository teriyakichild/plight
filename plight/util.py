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

PID_FILE = PIDLockFile('/var/run/plight/plight.pid')


def get_config(config_file=plight.CONFIG_FILE):
    parser = ConfigParser.ConfigParser()
    parser.read(config_file)
    config = {
        'host': parser.get('webserver', 'host'),
        'port': parser.getint('webserver', 'port'),
        'user': parser.get('webserver', 'user'),
        'group': parser.get('webserver', 'group'),
        'web_log_file': parser.get('webserver', 'logfile'),
        'web_log_level': getattr(logging,
                                 parser.get('webserver', 'loglevel')),
        'web_log_filesize': parser.getint('webserver', 'filesize'),
        'web_log_rotation_count': parser.getint('webserver', 'rotationcount'),
        'log_file': parser.get('logging', 'logfile'),
        'log_level': getattr(logging,
                             parser.get('logging', 'loglevel')),
        'log_filesize': parser.getint('logging', 'filesize'),
        'log_rotation_count': parser.getint('logging', 'rotationcount')
    }
    logger = logging.getLogger('plight')
    logger.setLevel(config['log_level'])
    config['states'] = process_states_from_config(parser, logger)
    return config


def process_states_from_config(parser, logger):
    # The old state_file setup was the true/false existance
    # of state_file. If the old configuration setup is being used,
    # we want to reproduce that behavior. The definition of
    # state_file will act as old vs new configuration key.
    state_file = None
    # Load in the default states
    states = plight.STATES
    try:
        state_file = parser.get('permanents', 'statefile')
    except ConfigParser.NoSectionError:
        pass
    if state_file is not None:
        logger.warn('Permanents section is deprecated, see release notes')
        states['disabled']['file'] = state_file
        states['disabled']['old_config'] = True
        states.pop('offline', None)
    if 'old_config' not in states['disabled']:
        # We are on the new config.  Valid states are pulled
        # from the defined priorities.states, which should be ordered
        # from lowest to highest priority.
        err = None
        try:
            priorities = parser.get('priorities', 'states').split(',')
        except ConfigParser.NoSectionError:
            err = 'No priorities section defined in config file'
        except ConfigParser.NoOptionError:
            err = 'Missing states option in priorities section of config file'
        finally:
            if err:
                logger.error(err)
                raise Exception(err)
        # Based on the defined priorties we want to remove unused states
        keep_states = {}
        for state in states:
            if state in priorities:
                keep_states[state] = states[state]
        states = keep_states
        # Now we want to loop through the requested states
        for state in priorities:
            # Error if values aren't provided
            if not parser.has_section(state) and state not in states:
                err = 'Priorities contains undefined state {0}'.format(state)
                logger.error(err)
                raise Exception(err)
            if state not in states:
                states[state] = {'priority': priorities.index(state)}
            for option in plight.STATES['enabled']:
                try:
                    states[state][option] = parser.get(state, option)
                except ConfigParser.NoOptionError:
                    if option in ['command', 'priority']:
                        continue
                    if option == 'file':
                        states[state][option] = None
                        continue
                    raise
                try:
                    states[state][option] = int(states[state][option])
                except ValueError:
                    pass
    return states


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
    if PID_FILE.is_locked():
        sys.stderr.write('Plight is already running\n')
        sys.exit(1)

    context = DaemonContext(pidfile=PID_FILE,
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
    if PID_FILE.is_locked():
        pid = PID_FILE.read_pid()
        os.kill(int(pid), signal.SIGTERM)
    else:
        print('no pid file available')


def format_get_current_state(state, details):
    warning = ''
    if not PID_FILE.is_locked():
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
    config = get_config()
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
