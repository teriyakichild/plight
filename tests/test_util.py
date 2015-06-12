import pytest
import plight
import plight.util as util

def test_get_config(config_file):
    config = util.get_config(config_file)
    assert config
    assert config['host'] == '0.0.0.0'
    assert config['port'] == 10101
    assert config['web_log_file'] == '/var/log/plight/access.log'
    assert config['log_file'] == '/var/log/plight/plight.log'
    if 'enabled' in config['states']:
        state = config['states']['enabled']
        assert state['file'] == None
        assert state['code'] == 200
        assert state['priority'] == 0

    if 'disabled' in myconfig['states']:
        state = myconfig['states']['disabled']
        assert state['file'] == '/var/lib/plight/node_disabled'
        if 'old_config' in state and state['old_config']:
            assert state['code'] == 404
        else:
            assert state['code'] == 200
        assert state['command'] == 'disable'
        assert state['priority'] == 1

    if 'offline' in myconfig['states']:
        state = myconfig['states']['offline']
        assert state['file'] == '/var/lib/plight/node_offline'
        assert state['code'] == 200
        assert state['priority'] == 2

    if 'master' in myconfig['states']:
        state = myconfig['states']['master']
        assert state['file'] == None
        assert state['code'] == 200
        assert state['priority'] == 0

    if 'slave' in myconfig['states']:
        state = myconfig['states']['slave']
        assert state['file'] == '/var/lib/plight/node_slave'
        assert state['code'] == 200
        assert state['priority'] == 1

def test_format_list_states(capsys, states):
    check = ''
    for state, details in states.items():
        if details['file'] is None:
            message_modifier = ' [default]'
        else:
            message_modifier = ''
        check += 'State: {0}{1}\nCode: {2}\nMessage: {3}\n\n'.format(
            state, message_modifier, details['code'], details['message'])

    util.format_list_states('enabled', states)
    out, err = capsys.readouterr()
    assert out == check

def test_running_format_get_current_state(capsys, states, pidfile):
    if not pidfile.is_locked():
        pidfile.acquire()
    check = ''
    for state, details in states.items():
        message = 'State: {0}\nCode: {1}\nMessage: {2}\n'
        check = message.format(state, details['code'], details['message'])
        util.format_get_current_state(state, details)
        out, err = capsys.readouterr()
        assert out == check
    if pidfile.is_locked():
        pidfile.release()

def test_stopped_format_get_current_state(capsys, states, pidfile):
    if pidfile.is_locked():
        pidfile.release()
    check = ''
    for state, details in states.items():
        warning = 'WARNING: plight is not running\n'
        message = '{0}State: {1}\nCode: {2}\nMessage: {3}\n'
        check = message.format(
                    warning, state, details['code'], details['message'])
        util.format_get_current_state(state, details)
        out, err = capsys.readouterr()
        assert out == check
