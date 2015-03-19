#
# Copyright (c) 2015, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
#   Neither the name of Arista Networks nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

""" Controller for Arista EOS command API (eAPI)

The eapictl provides a remote controller for configuring and managing
Arista EOS eAPI.   The controller works by establishing an SSH connection
to a destination node for the purpose of managing the eAPI service.

Example:

    # enable eAPI using the current configuration
    $ eapictl start veos01

    # disable eAPI on the destination node
    $ eapictl stop veos01

    # get the current status of eapi
    $ eapictl status veos01

    # override the conf file settings
    $ eapictl enable veos01 --username sshuser --password sshpassword

"""
import re
import socket
import argparse
import json
import time

from StringIO import StringIO

import paramiko

import pyeapi

from pyeapi.client import DEFAULT_TRANSPORT

DEFAULT_SSH_PORT = 22
DEFAULT_SSH_USERNAME = 'admin'
DEFAULT_SSH_PASSWORD = ''

DEFAULT_HTTP_PORT = '80'
DEFAULT_HTTPS_PORT = '443'

DEFAULT_POLL_TIMEOUT = 10
DEFAULT_CONNECTION_TIMEOUT = 10

PROMPT_RE = [
    re.compile(r"[\r\n]?[\w+\-\.:\/]+(?:\([^\)]+\)){,3}(?:>|#) ?$"),
    re.compile(r"\[\w+\@[\w\-\.]+(?: [^\]])\] ?[>#\$] ?$")
]


def connect_ssh(hostname, username, password):
    """ Creates the SSH connection to the specified host

    Args:
        hostname (str): The IP address or fully qualified domain name of the
            destination node to connect to
        username (str): The username used to authenticate the SSH connection
        password (str): The password used to authenticate the SSH connection

    Returns:
        SSHClient: An instance of paramiko.SSHClient

    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password)
    return ssh

def check_prompt(string):
    """ Checks the specified string against known EOS prompts

    Args:
        string (str): The prompt string to check

    Returns:
        True: If the string includes a valid EOS prompt

    """
    for regex in PROMPT_RE:
        match = regex.search(string)
        if match:
            return True

class Ssh(object):
    """ Manages the SSH connection to a remote node

    The Ssh class provides an instance for communicating with the remote node
    over the SSH protocool.  The instance allows for sending and receving
    commands over SSH.

    Attributes:
        hostname (str): The hostname of the destination node
        ssh (SSHClient): An instance of paramiko.SSHClient
        timeout (int): The timeout value for connecting to the remote node
        channel: The SSH shell channel invoked over the SSH transport

    Args:
        hostname (str): The hostanem of the destination node
        username (str): The username to authenticate the SSH session
        password (str): The password to authenticate the SSH session
        timeout (int): The connection timeout value.  Default value is 10secs
    """

    def __init__(self, hostname, username, password, timeout=10):
        self.hostname = hostname
        self.ssh = connect_ssh(hostname, username, password)

        self.timeout = timeout
        self.channel = None

    @property
    def shell(self):
        if self.channel is None:
            self.channel = self.ssh.invoke_shell()
            self.channel.settimeout(self.timeout)
        return self.channel

    def send(self, command):
        command += '\n'
        self.shell.sendall(str(command))

        cache = StringIO()
        response = ''

        while True:
            try:
                response = self.shell.recv(200)
            except socket.timeout:
                raise IOError('Socket timeout for host %s' % self.hostname)

            cache.write(response)
            if check_prompt(response):
                return cache.getvalue()

    def sendall(self, commands):
        return [self.send(c) for c in commands]

    def send_enable(self, commands):
        commands.insert(0, 'enable')
        response = self.sendall(commands)
        return response

    def send_config(self, commands):
        commands.insert(0, 'configure')
        response = self.send_enable(commands)
        self.send('enable 0')
        return response

    def close(self):
        self.ssh.close()

class Eapi(object):
    """ Manages the eAPI configuration and state information

    The Eapi class provides an instance that includes both the current
    state of eAPI derived from the node and provides an instance for
    configuring eAPI over an SSH transport.

    Args:
        ssh(Ssh): The instance of Ssh used to send and receive commands to
            the destination node

    """

    def __init__(self, ssh):
        self._ssh = ssh

    def status(self):
        cmd = ['show management api http-commands']
        output = self._ssh.send_enable(cmd)
        output = output[1]

        status = dict()
        status['enabled'] = parse_enabled_state(output)
        status['http'] = parse_http_state(output)
        status['http_port'] = parse_http_port(output)
        status['https'] = parse_https_state(output)
        status['https_port'] = parse_https_port(output)
        return status

    def isenabled(self):
        status = self.status()
        return status['enabled']

    def isrunning(self):
        status = self.status()
        http = status['http']
        https = status['https']
        return http == 'running' or https == 'running'

    def isstopped(self):
        status = self.status()
        http = status['http']
        https = status['https']
        notrunning = ['shutdown', 'enabled']
        return (http in notrunning) and (https in notrunning)

    def enable(self):
        commands = ['management api http-commands', 'no shutdown']
        return self._ssh.send_config(commands)

    def disable(self):
        commands = ['management api http-commands', 'shutdown']
        return self._ssh.send_config(commands)

    def set_protocol(self, protocol, port=None):
        if protocol not in ['http', 'https']:
            raise TypeError('Protocol must be one of "http" or "https"')

        if not port:
            port = default_port(protocol)

        cmds = ['management api http-commands']
        if protocol == 'http':
            cmds += ['no protocol https', 'protocol http port %s' % port]
        elif protocol == 'https':
            cmds += ['no protocol http', 'protocol https port %s' % port]
        return self._ssh.send_config(cmds)


def default_port(protocol):
    """ Returns the default port based on the protocol

    Args:
        protocol (str): The protocol to return the default port for.  Valid
            values are "http" and "https"

    Returns:
        str: The default protocol port value as a string

    """
    return '443' if protocol == 'https' else '80'

def parse_enabled_state(output):
    """ Parses the show command for the eAPI status

    Args:
        output (str): Output from show management api http-commands

    Returns:
        bool: True if eAPI is enabled otherwise False

    """
    status = re.search(r'Enabled:\s+(\w+)', output)
    return status.group(1) == 'Yes'

def parse_http_state(output):
    """ Parses the show command for the eAPI status

    Args:
        output (str): Output from show management api http-commands

    Returns:
        str: The current state value for HTTP Server

    """
    status = re.search(r'HTTP server:\s+(\w+)', output)
    return status.group(1)

def parse_http_port(output):
    """ Parses the show command for the eAPI status

    Args:
        output (str): Output from show management api http-commands

    Returns:
        str: The current state value for HTTP Server port

    """
    status = re.search(r'HTTP .* port (\d+)', output)
    return status.group(1)

def parse_https_state(output):
    """ Parses the show command for the eAPI status

    Args:
        output (str): Output from show management api http-commands

    Returns:
        str: The current state value for HTTPS Server

    """
    status = re.search(r'HTTPS server:\s+(\w+)', output)
    return status.group(1)

def parse_https_port(output):
    """ Parses the show command for the eAPI status

    Args:
        output (str): Output from show management api http-commands

    Returns:
        str: The current state value for HTTPS Server port

    """
    status = re.search(r'HTTPS .* port (\d+)', output)
    return status.group(1)

def enable_eapi(eapi, timeout=DEFAULT_POLL_TIMEOUT):
    """ Administratively enables eAPI on the destination node

    Args:
        eapi: The instance of Eapi
        timeout (int): Polling interval to watch for status change

    Raises:
        RuntimeWarning: Raises if the poll timeout interval expires before
            the staus change.  This does not mean the change did not finish
    """
    eapi.enable()
    while True:
        if eapi.isrunning():
            return
        time.sleep(1)
        timeout -= 1
        if timeout == 0:
            raise RuntimeWarning


def disable_eapi(eapi, timeout=DEFAULT_POLL_TIMEOUT):
    """ Administratively disables eAPI on the destination node

    Args:
        eapi: The instance of Eapi
        timeout (int): Polling interval to watch for status change

    Raises:
        RuntimeWarning: Raises if the poll timeout interval expires before
            the staus change.  This does not mean the change did not finish
    """
    eapi.disable()
    while True:
        if eapi.isstopped():
            return
        time.sleep(1)
        timeout -= 1
        if timeout == 0:
            raise RuntimeWarning


def parse_args(args):
    """ Handles parsing of the command line arguments

    Args:
        args (list): The list of arguments provided by the command line

    Returns:
        Namespace: An instance of Namespace generate by argparse
    """

    parser = argparse.ArgumentParser()

    parser.add_argument('action',
                        choices=['start', 'stop', 'status', 'restart'],
                        help='Specifies the action to perform on the '
                             'destination node')

    parser.add_argument('connection',
                        help='Specifies the name of the node.  This is the '
                             'name of the connection profile to load')

    parser.add_argument('--config',
                        help='Overrides the default eapi.conf')

    parser.add_argument('--host',
                        help='Overrides the hostname or IP address of the '
                             'destination node to configure')

    parser.add_argument('--username', '-u',
                        default=DEFAULT_SSH_USERNAME,
                        help='Overrides the SSH username to use')

    parser.add_argument('--password', '-p',
                        default=DEFAULT_SSH_PASSWORD,
                        help='Overrides the SSH password to use')

    parser.add_argument('--server-port',
                        default=DEFAULT_SSH_PORT,
                        help='Overrides the SSH port to connect to on the '
                             'destination node')

    parser.add_argument('--transport',
                        choices=['http', 'https'],
                        help='Overrides the transport setting for eAPI')

    parser.add_argument('--eapi-port',
                        help='Overrides the eAPI transport endpoint port')

    parser.add_argument('--poll-timeout',
                        default=DEFAULT_POLL_TIMEOUT,
                        help='Sets the timeout value waiting for eAPI to '
                             'be enabled')

    parser.add_argument('--connection-timeout',
                        default=DEFAULT_CONNECTION_TIMEOUT,
                        help='Sets the connection timeout value for '
                             'establishing SSH connections')

    return parser.parse_args(args)

def main(args=None):
    """The eapictl main routine

    Args:
        args (list): The list of command line args

    Returns:
        0: If the application completed successfully

        2: If there as an error during the transaction

    """

    retcode = 0
    args = parse_args(args)

    if args.config:
        pyeapi.load_config(args.config)

    config = pyeapi.config_for(args.connection)
    if config is None:
        config = dict(host=args.connection)

    for key in ['host', 'server_port', 'username', 'password']:
        if getattr(args, key) is not None:
            config[key] = getattr(args, key)

    ssh = Ssh(config['host'], config['username'], config['password'],
              timeout=args.connection_timeout)

    eapi = Eapi(ssh)

    proto = args.transport or config.get('transport', DEFAULT_TRANSPORT)
    port = args.eapi_port or config.get('port', default_port(proto))

    try:
        if args.action == 'start':
            if not eapi.isenabled():
                eapi.set_protocol(proto, port)
                enable_eapi(eapi, args.poll_timeout)
        elif args.action == 'stop':
            if eapi.isenabled():
                disable_eapi(eapi, args.poll_timeout)
        elif args.action == 'restart':
            eapi.set_protocol(proto, port)
            disable_eapi(eapi, args.poll_timeout)
            enable_eapi(eapi, args.poll_timeout)
    except RuntimeWarning:
        print 'Warning: Poll timeout expired before eAPI operation completed'
        retcode = 2

    print json.dumps(eapi.status())

    ssh.close()

    return retcode



