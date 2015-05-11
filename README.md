# Plight [![Build Status](https://travis-ci.org/rackerlabs/plight.svg?branch=master)](https://travis-ci.org/rackerlabs/plight)
An application agnostic tool to represent node availability.

## What is this nonsense?
In many of our deploment pipelines we had to gather credentials from any number of systems,
such as load balancers and monitoring, to disable nodes.  Each system might have different
requirements for authentication, vary quality of APIs or automation libraries, etc.  With
stricter RBAC requirements we sometime ran into a system that required admin access to do
a simple state change.  Aside from the cumbersome credentials management, access levels
can be a problem in more compliance-oriented environments.

Most of these external systems did have some means of internally managing the state, whether
via health checks or some other function.  Thus our initial approach was to work with our
developers to enable some kind of health state in their applications that we could configure
our systems to utilize.  However, this path leaves "off the shelf" software without a path.

Once we tried to cover all of our use cases we decided the best route would be to separate
this functionality into a separate standalone web service.

## Why is it called Plight?
    a dangerous, difficult, or otherwise unfortunate situation

Originally called the 'nodestatus', we took to the thesaurus. Based one where we were with
the original path to solve this problem we landed on plight.

## Installation

### Fedora or EL-based:
We have a [COPR](http://copr-fe.cloud.fedoraproject.org/coprs/xaeth/Plight) that is kept current with releases. After enabling that repository install using:
```yum install plight```

### From source
```make install```

## Configuration

### Enable the service
```
chkconfig plightd on
service plightd start
```

  or

```
systemctl enable plightd
systemctl start plightd
```

### States
By default Plight comes with 3 explicit states, which as of the 0.1.0 series are configurable in ```plight.conf```.

State   | Status Code | Message
--------|-------------|--------
Enabled | 200         | node is available
Disabled| 404         | node is unavailable
Offline | 503         | node is offline

Long term we are going to change the Status codes to default to 200 for these three states.
We maintained the states from the previous release for compatability purposes.

### Changing states
Using ```plight --help``` from the cli will give you a list of all valid plight commands, which includes start, stop, and a dynamically generated list based on configured states.

#### Put a mode into maintenance mode
```plight disable```

#### Put a mode into offline mode
```plight offline```

#### Return a node to active mode
```plight enable```

#### Checking the current state of a node
```curl http://localhost:10101 -D -```

# Licensing
All files contained with this distribution are licenced either under the [Apache License v2.0](http://www.apache.org/licenses/LICENSE-2.0) or the [GNU General Public License v2.0](http://www.gnu.org/licenses/gpl-2.0.html). You must agree to the terms of these licenses and abide by them before viewing, utilizing, modifying, or distributing the source code contained within this distribution.

# Build Notes
If building on el5, you will need to have buildsys-macros installed.
