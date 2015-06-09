import pytest
import os
import plight.util as util


GENERIC_OLD_CONFIG="""
[webserver]
port = 10101
host = 0.0.0.0
user = plight
group = plight
logfile = /var/log/plight/access.log
loglevel = INFO
filesize = 1024000
rotationcount = 10

[logging]
logfile = /var/log/plight/plight.log
loglevel = INFO
filesize = 1024000
rotationcount = 10

[permanents]
statefile = /var/lib/plight/node_disabled
"""

GENERIC_CONFIG="""
[webserver]
port = 10101
host = 0.0.0.0
user = plight
group = plight
logfile = /var/log/plight/access.log
loglevel = INFO
filesize = 1024000
rotationcount = 10

[logging]
logfile = /var/log/plight/plight.log
loglevel = INFO
filesize = 1024000
rotationcount = 10

[priorities]
states=enabled,disabled,offline

[disabled]
file = /var/lib/plight/node_disabled
command = disable
code = 200
message = node is unavailable

[enabled]
command = enable
code = 200
message = node is available

[offline]
file = /var/lib/plight/node_offline
code = 200
message = node is offline
"""

ALTERNATE_CONFIG="""
[webserver]
port = 10101
host = 0.0.0.0
user = plight
group = plight
logfile = /var/log/plight/access.log
loglevel = INFO
filesize = 1024000
rotationcount = 10

[logging]
logfile = /var/log/plight/plight.log
loglevel = INFO
filesize = 1024000
rotationcount = 10

[priorities]
states=master,slave,offline

[master]
code = 200
message = master node

[slave]
file = /var/lib/plight/node_slave
code = 200
message = slave node

[offline]
file = /var/lib/plight/node_offline

code = 200
message = node is offline
"""


@pytest.fixture(scope='function',
                params=[GENERIC_OLD_CONFIG,
                        GENERIC_CONFIG,
                        ALTERNATE_CONFIG])
def config_file(request, tmpdir):
    file = tmpdir.join('config')
    open(file.strpath, 'w').write(request.param)
    return file.strpath


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

    if 'disabled' in config['states']:
        state = config['states']['disabled']
        assert state['file'] == '/var/lib/plight/node_disabled'
        if 'old_config' in state and state['old_config']:
            assert state['code'] == 404
        else:
            assert state['code'] == 200
        assert state['command'] == 'disable'
        assert state['priority'] == 1

    if 'offline' in config['states']:
        state = config['states']['offline']
        assert state['file'] == '/var/lib/plight/node_offline'
        assert state['code'] == 200
        assert state['priority'] == 2

    if 'master' in config['states']:
        state = config['states']['master']
        assert state['file'] == None
        assert state['code'] == 200
        assert state['priority'] == 0

    if 'slave' in config['states']:
        state = config['states']['slave']
        assert state['file'] == '/var/lib/plight/node_slave'
        assert state['code'] == 200
        assert state['priority'] == 1

def test_format_list_states(capsys, config_file):
    config = util.get_config(config_file)
    states = config['states']
    check = ''
    for state, details in states.items():
        if details['file'] is None:
            message_modifier = ' [default]'
        else:
            message_modifier = ''
        check += 'State: {0}{1}\nCode: {2}\nMessage: {3}\n\n'.format(
            state, message_modifier, details['code'], details['message'])

    util.format_list_states('enabled', config['states'])
    out, err = capsys.readouterr()
    assert out == check
    
    
@pytest.fixture
def pidfile(tmpdir):
    try:
        from daemon.pidlockfile import PIDLockFile
    except ImportError:
        from daemon.pidfile import PIDLockFile
    # Create a tmpdir for the pidfile and overwrite 
    # the current util.PID_FILE constant
    util.PID_FILE = tmpdir.join('plight.pid').strpath
    return PIDLockFile(util.PID_FILE)


def test_running_format_get_current_state(capsys, config_file, pidfile):
    if not pidfile.is_locked():
        pidfile.acquire()
    config = util.get_config(config_file)
    states = config['states']
    check = ''
    for state, details in states.items():
        message = 'State: {0}\nCode: {1}\nMessage: {2}\n'
        check = message.format(state, details['code'], details['message'])
        util.format_get_current_state(state, details)
        out, err = capsys.readouterr()
        assert out == check
    if pidfile.is_locked():
        pidfile.release()

def test_stopped_format_get_current_state(capsys, config_file, pidfile):
    if pidfile.is_locked():
        pidfile.release()
    config = util.get_config(config_file)
    states = config['states']
    check = ''
    for state, details in states.items():
        warning = 'WARNING: plight is not running\n'
        message = '{0}State: {1}\nCode: {2}\nMessage: {3}\n'
        check = message.format(
                    warning, state, details['code'], details['message'])
        util.format_get_current_state(state, details)
        out, err = capsys.readouterr()
        assert out == check


