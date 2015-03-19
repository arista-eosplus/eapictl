import unittest
import os
import json
import shlex

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))

from StringIO import StringIO

from systestlib import get_fixture

import eapictl.app

class TestStatus(unittest.TestCase):

    def setUp(self):
        self.stdout = sys.stdout
        sys.stdout = StringIO()
        self.connection = open(get_fixture('dut')).readlines()[0]
        self.config = get_fixture('eapi.conf')

    def tearDown(self):
        sys.stdout = self.stdout

    def runcmd(self, cmdline):
        cmdline = str(cmdline).format(connection=self.connection)
        cmdline = shlex.split(cmdline)
        cmdline.extend(['--config', self.config])
        eapictl.app.main(cmdline)

    def test_status_command(self):
        """ status {connection}
        """
        keys = ['http', 'http_port', 'enabled', 'https_port', 'https']
        self.runcmd('status {connection}')
        resp = json.loads(sys.stdout.getvalue())
        self.assertEqual(sorted(resp.keys()), sorted(keys))

    def test_start_command(self):
        self.runcmd('stop {connection}')
        self.runcmd('start {connection}')
        output = sys.stdout.getvalue().split('\n')
        resp = json.loads(output[1])
        self.assertTrue(resp['enabled'])

    def test_stop_command(self):
        self.runcmd('start {connection}')
        self.runcmd('stop {connection}')
        output = sys.stdout.getvalue().split('\n')
        resp = json.loads(output[1])
        self.assertFalse(resp['enabled'])

    def test_configure_transport_http(self):
        """ restart {connection} --transport http
        """
        self.runcmd('restart {connection} --transport http')
        output = sys.stdout.getvalue()
        resp = json.loads(output)
        self.assertEqual(resp['http'], 'running')

    def test_configure_transport_https(self):
        """ restart {connection} --transport https
        """
        self.runcmd('restart {connection} --transport https')
        output = sys.stdout.getvalue()
        resp = json.loads(output)
        self.assertEqual(resp['https'], 'running')

    def test_configure_server_port(self):
        """ restart {connection} --transport http --eapi-port 8080
        """
        self.runcmd('restart {connection} --transport http --eapi-port 8080')
        output = sys.stdout.getvalue()
        resp = json.loads(output)
        self.assertEqual(resp['http_port'], '8080')







if __name__ == '__main__':
    unittest.main()

