import pytest
import os
import plight.util as util


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

[permanents]
statefile = /var/lib/plight/node_disabled
"""

@pytest.fixture(scope='function',
                params=[GENERIC_CONFIG])
def config_file(request, tmpdir):
    file = tmpdir.join('config')
    open(file.strpath, 'w').write(request.param)
    return file.strpath


def test_get_config(config_file):
    assert util.get_config(config_file)
