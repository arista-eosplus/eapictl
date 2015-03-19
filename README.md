# Arista eAPI Controller

#### Table of Contents

1. [Overview] (#overview)
    * [Requirements] (#requirements)
    * [Known Caveats] (#known-caveats)
2. [Getting Started] (#getting-started)
3. [Installation] (#installation)
4. [Testing] (#testing)
5. [Contributing] (#contributing)
6. [License] (#license)

The Arista eAPI Controller is a small untility application that can be used to
remotely configure and enable eAPI.  By default, all Arista EOS nodes since the
introduction of eAPI come with eAPI disabled by default.   In order to provide
a more seamless, automated approach to working with eAPI, this utility will
allow an operator to configure and enable eAPI in order to start communicting
with the node using API calls.

This library is freely provided to the open source community for building
robust applications using Arista EOS.  Support is provided as best effort
through [Github issues](http://github.com/arista-eosplus/eapictl/issues).

## Requirements

* Arista EOS 4.12 or later with valid SSH credentials
* Pytho 2.7
* Paramiko 
* Python client for eAPI (optional)

## Known Caveats

The initial release of eapictl has the following known caveats:

* Only supports http and https transports.  Support for socket and http_local
  to be added in a later release
* Only supported as a remote (off-box) application
* Supports only username / password authentication mechanisms


# GETTING STARTED

Using the Arista eAPI controller is easy.  Once installed (see
[INSTALLATION](#installation), use the eapictl application to configure, enable
and/or disable eAPI.

```
# show the current status and configuration
$ eapictl status 192.168.1.16 --username admin --password mysecret
{"http": "enabled", "http_port": "80", "enabled": false, "https_port": "443",
"https": "shutdown"}

# start eAPI on the remote node
$ eapictl start 192.168.1.16 --username admin --password mysecret
{"http": "enabled", "http_port": "80", "enabled": true, "https_port": "443",
"https": "shutdown"}

# stop eAPI on the remote node
$ eapictl stop 192.168.1.16 --username admin --password mysecret
{"http": "enabled", "http_port": "80", "enabled": false, "https_port": "443",
"https": "shutdown"}

```

The Arista eAPI controller also works with connection profiles configure for
[Python Client for eAPI](http://github.com/arista-eosplus/pyeapi).  When the
eapi.conf file is configure (or passed by command line option), eapictl will
cofigure eAPI per the eapi.conf file. 

```
$ cat ~/.eapi.conf
[connection:veos01]
host: 192.168.1.16
username: eapi
password: password
transport: http
port: 8080

# start eAPI
$ eapictl start veos
{"http": "enabled", "http_port": "8080", "enabled": true, "https_port": "443",
"https": "shutdown"}

# stop eAPI
$ eapictl stop veos
{"http": "enabled", "http_port": "80", "enabled": false, "https_port": "443",
"https": "shutdown"}

```

# INSTALLATION

The source code for eapictl is provided on Github at 
http://github.com/arista-eosplus/eapictl.  All current development is done in
the 'develop' branch.  Stable versions for release are tagged in the master
branch and uploaded to PyPi

* To install the latest stable version of eapictl, simply run ``pip install
  eapictl`` (or ``pip install --upgrade eapictl``)

* To install the latest development version from Github, simply clone the
  develop branch and run ``python setup.py install`` from the cloned folder.

# TESTING

There are two types of tests provided with eapictl, unit and system.  Unit
tests do not currently cover the entire application but can be run without an
end system.  Coversely system tests provide 100% coverage but require a node
(either physical or vEOS) to test against.

To run either sets of tests, start by setting up the development enviornment
using pip.

```
$ pip install -r dev-requirements.txt
```

Once completed, run the unit tests using make:

```
$ make unittests
```

If you want to run the system tests, you need to update two files.  The first
file is test/fixtures/eapi.conf to include the necessary profile for connecting
to the remote node.   The second file is /test/fixtures/dut which should just
be the connection profile to load.  Once updated, execute the system tests
using make again

```
$ make systests
```

# CONTRIBUTING

Contributing pull requests are gladly welcomed for this repository.  Please
note that all contributions that modify the client behavior require
corresponding test cases otherwise the pull request will be rejected.

# LICENSE

Copyright (c) 2015, Arista Networks EOS+
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the Arista nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.




