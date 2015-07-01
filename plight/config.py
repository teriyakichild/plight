#!/usr/bin/env python

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser
import logging

STATES = {
    'enabled': {
        'command': 'enable',
        'file': None,
        'code': 200,
        'message': 'OK',
        'priority': 0
    },
    'disabled': {
        'command': 'disable',
        'file': '/var/tmp/node_disabled',
        'code': 404,
        'message': 'node is unavailable',
        'priority': 1
    },
    'offline': {
        'file': '/var/tmp/node_offline',
        'code': 503,
        'message': 'node is offline',
        'priority': 2
    },
}
CONFIG_FILE = '/etc/plight.conf'
PID_FILE = '/var/run/plight/plight.pid'


def get_config(config_file=CONFIG_FILE):
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
    states = STATES
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
            for option in STATES['enabled']:
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
