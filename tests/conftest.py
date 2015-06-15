import pytest
import os
import plight
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
statefile = /var/tmp/node_disabled
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
file = /var/tmp/node_disabled
command = disable
code = 200
message = node is unavailable

[enabled]
command = enable
code = 200
message = node is available

[offline]
file = /var/tmp/node_offline
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
file = /var/tmp/node_slave
code = 200
message = slave node

[offline]
file = /var/tmp/node_offline
code = 200
message = node is offline
"""


@pytest.fixture(scope='function',
                params=[GENERIC_OLD_CONFIG,
                        GENERIC_CONFIG,
                        ALTERNATE_CONFIG])
def config(request, tmpdir):
    file = tmpdir.join('config')
    open(file.strpath, 'w').write(request.param)
    return util.get_config(file.strpath)

@pytest.fixture(scope='function')
def states(config):
    return config['states']

@pytest.fixture(scope='function')
def status(request, states):
    status = plight.NodeStatus(states)
    def reset():
        status.set_node_enabled()
    request.addfinalizer(reset)
    return status

@pytest.fixture(scope='module')
def pidfile(tmpdir):
    try:
        from daemon.pidlockfile import PIDLockFile
    except ImportError:
        from daemon.pidfile import PIDLockFile
    # Create a tmpdir for the pidfile and overwrite
    # the current util.PID_FILE constant
    util.PID_FILE = PIDLockFile(tmpdir.join('plight.pid').strpath)
    return util.PID_FILE
