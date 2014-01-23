#!/usr/bin/python

from setuptools import setup

import sys
sys.path.insert(0, '.')

from plight import __version__, __author__, __author_email__, __license__

NAME = "plight"
SHORT_DESC = "Python bindings or interacting with PasswordSafe API"


if __name__ == "__main__":
 
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
        install_requires = ['cherrypy'],
        entry_points={
            'console_scripts': [ 'plight = plight.util:run' ],
        },
        data_files=[('/etc/rc.d/init.d', ['scripts/plightd.init']),
                    ('/etc', ['plight.conf'])]
    )
