from __future__ import absolute_import, print_function
from base64 import b64encode
from failover import ApachePasswdFileCheck, ok, Oneshot
import logging
from os.path import dirname
from six.moves.http_client import (
    HTTPConnection, INTERNAL_SERVER_ERROR, OK, NOT_FOUND, SERVICE_UNAVAILABLE,
    UNAUTHORIZED)
from sys import stderr
from time import sleep
from unittest import TestCase, main
from .server import create_server, start_server, stop_server

LOOPBACK = "127.0.0.1"

class OneshotTest(TestCase):
    def setUp(self):
        logging.basicConfig(
            stream=stderr, level=logging.DEBUG,
            format=("%(asctime)s %(module)s [%(levelname)s] "
                    "%(filename)s:%(lineno)d: %(message)s"))

    def test_oneshot(self):
        checker = Oneshot(name="oneshot1")
        self.assertFalse(checker())
        self.assertFalse(checker())
        
        # Arm the checker -- should get exactly one positive response.
        checker.fire()
        self.assertTrue(checker())
        self.assertFalse(checker())

        # Check the name
        self.assertEqual(repr(checker), "oneshot1")
        checker.name = None
        self.assertTrue(repr(checker).startswith("<failover.oneshot.Oneshot"))
        return

    def test_dummy_auth(self):
        self.auth_result = True
        def dummy_auth():
            return self.auth_result

        checker = Oneshot(default_state=ok, auth=dummy_auth)
        self.assertTrue(checker())
        self.assertTrue(checker())
        
        # Arm the checker -- should get exactly one fail response.
        checker.fire()
        self.assertFalse(checker())
        self.assertTrue(checker())

        # Try to arm the checker, but fail the auth.  No change should result.
        self.auth_result = False
        checker.fire()
        self.assertTrue(checker())
        return

    def test_server_auth(self):
        # htpasswd.test has three users, all with password 'passw0rd',
        # encrypted with different algorithms
        auth = ApachePasswdFileCheck(dirname(__file__) + "/htpasswd.test")
        checker = Oneshot(default_state=ok, auth=auth)

        server = create_server()
        start_server(server)

        try:
            server.add_component("oneshot", task=checker, on_post=checker.fire)
            
            con = HTTPConnection(LOOPBACK, server.port)
            con.request("GET", "/oneshot")
            response = con.getresponse()
            self.assertEqual(response.status, OK)

            # Arm the checker -- should get exactly one fail response
            for username in ("testmd5", "testsha", "testcrypt"):
                authhdr = "Basic " + b64encode(username + ":passw0rd")
                con.request("POST", "/oneshot", "", {"Authorization": authhdr})
                response = con.getresponse()
                self.assertEqual(response.status, OK)

                con.request("GET", "/oneshot")
                response = con.getresponse()
                self.assertEqual(response.status, SERVICE_UNAVAILABLE)

                con.request("GET", "/oneshot")
                response = con.getresponse()
                self.assertEqual(response.status, OK)

            # Fail to arm without auth
            con.request("POST", "/oneshot", "")
            response = con.getresponse()
            self.assertEqual(response.status, UNAUTHORIZED)

            # Fail to arm with bogus auth header
            con.request("POST", "/oneshot", "", {"Authorization": "1234"})
            response = con.getresponse()
            self.assertEqual(response.status, UNAUTHORIZED)

            # Fail to arm with bad passwords
            for username in ("testmd5", "testsha", "testcrypt"):
                authhdr = "Basic " + b64encode(username + ":foobar")
                con.request("POST", "/oneshot", "", {"Authorization": authhdr})
                response = con.getresponse()
                self.assertEqual(response.status, UNAUTHORIZED)

            # Fail to arm with unknown auth method
            con.request("POST", "/oneshot", "",
                        {"Authorization": "Negotiate foobar"})
            response = con.getresponse()
            self.assertEqual(response.status, UNAUTHORIZED)

            # Fail to arm with bogus base64 data
            con.request("POST", "/oneshot", "",
                        {"Authorization": "Basic `'[]"})
            response = con.getresponse()
            self.assertEqual(response.status, UNAUTHORIZED)
            
            # Fail to arm with an unknown filename
            auth.filename = auth.filename + ".unknown"
            authhdr = "Basic " + b64encode("testsha:passw0rd")
            con.request("POST", "/oneshot", "", {"Authorization": authhdr})
            response = con.getresponse()
            self.assertEqual(response.status, INTERNAL_SERVER_ERROR)

            # Fail to arm with syntactically incorrect file
            auth.filename = dirname(__file__ + "/htpasswd.bad")
            authhdr = "Basic " + b64encode("testsha:passw0rd")
            con.request("POST", "/oneshot", "", {"Authorization": authhdr})
            response = con.getresponse()
            self.assertEqual(response.status, UNAUTHORIZED)
        finally:
            stop_server(server)

    def test_fail_auth_without_handler(self):
        checker = Oneshot(default_state=ok, auth=ApachePasswdFileCheck(
            dirname(__file__) + "/htpasswd.test"))
        try:
            checker.fire()
            self.fail("Expected RuntimeError")
        except RuntimeError:
            pass

