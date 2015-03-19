import os
import unittest
import shlex

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))

from mock import patch

from systestlib import get_fixture

import eapictl.app

class TestAppParser(unittest.TestCase):

    def _run_parser_test(self, cmdline):
        args = shlex.split(cmdline)
        return eapictl.app.parse_args(args)

    def test_parser_args(self):
        cmdline = open(get_fixture('cmdline')).readlines()
        for cmd in cmdline:
            result = self._run_parser_test(cmd)
            self.assertIsNotNone(result)

    def test_default_port_http(self):
        for proto, port in [('http', '80'), ('https', '443')]:
            result = eapictl.app.default_port(proto)
            self.assertEqual(result, port)

    def test_parse_enabled_state(self):
        config = open(get_fixture('show_cmd')).read()
        resp = eapictl.app.parse_enabled_state(config)
        self.assertTrue(resp)

    def test_parse_http_state(self):
        config = open(get_fixture('show_cmd')).read()
        resp = eapictl.app.parse_http_state(config)
        self.assertEqual(resp, 'running')

    def test_parse_http_port(self):
        config = open(get_fixture('show_cmd')).read()
        resp = eapictl.app.parse_http_port(config)
        self.assertEqual(resp, '80')

    def test_parse_https_state(self):
        config = open(get_fixture('show_cmd')).read()
        resp = eapictl.app.parse_https_state(config)
        self.assertEqual(resp, 'shutdown')

    def test_parse_https_port(self):
        config = open(get_fixture('show_cmd')).read()
        resp = eapictl.app.parse_https_port(config)
        self.assertEqual(resp, '443')

    def test_enable_eapi_success(self):
        with patch('eapictl.app.Eapi') as eapi_mock:
            instance = eapi_mock.return_value
            instance.isrunning.return_value = True

            try:
                eapictl.app.enable_eapi(instance, 2)
            except Exception as exc:
                self.fail(exc.message)

    def test_enable_eapi_timeout(self):
        with patch('eapictl.app.Eapi') as eapi_mock:
            instance = eapi_mock.return_value
            instance.isrunning.return_value = False

            with self.assertRaises(RuntimeWarning) as exc:
                eapictl.app.enable_eapi(instance, 2)

    def test_disable_eapi_success(self):
        with patch('eapictl.app.Eapi') as eapi_mock:
            instance = eapi_mock.return_value
            instance.isrunning.return_value = True

            try:
                eapictl.app.disable_eapi(instance, 2)
            except Exception as exc:
                self.fail(exc.message)

    def test_disable_eapi_timeout(self):
        with patch('eapictl.app.Eapi') as eapi_mock:
            instance = eapi_mock.return_value
            instance.isstopped.return_value = False

            with self.assertRaises(RuntimeWarning) as exc:
                eapictl.app.disable_eapi(instance, 2)

    def test_check_prompt(self):
        prompts = ['localhost>', 'localhost#', 'localhost(config)#',
                   'veos01(config-mgmt-api-http-cmds)#']

        for prompt in prompts:
            resp = eapictl.app.check_prompt('localhost>')
            self.assertTrue(prompt)



if __name__ == '__main__':
    unittest.main()
