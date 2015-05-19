#!/usr/bin/python

import os
from setuptools import setup

import sys
sys.path.insert(0, '.')

from plight import __version__, __author__, __author_email__, __license__

NAME = "plight"
SHORT_DESC = "Application and Load Balancer agnostic status tool"


if __name__ == "__main__":

    with open('requirements.txt') as f:
        required_pkgs = f.read().splitlines()

    setup(
        name = NAME,
        version = __version__,
        author = __author__,
        author_email = __author_email__,
        url = "https://github.com/rackerlabs/%s" % NAME,
        license = __license__,
        packages = [NAME],
        package_dir = {NAME: NAME},
        description = SHORT_DESC,
        entry_points={
            'console_scripts': [ 'plight = plight.util:run' ],
        },
        data_files=[('/etc/init.d', ['scripts/plightd.init']),
                    ('/usr/lib/systemd/system', ['scripts/plightd.service']),
                    ('/etc', ['plight.conf']),],
        install_requires = required_pkgs
    )
