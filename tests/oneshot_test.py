from __future__ import absolute_import, print_function
import failover
import logging
from six.moves.http_client import (
    HTTPConnection, OK, NOT_FOUND, SERVICE_UNAVAILABLE, UNAUTHORIZED)
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
        checker = failover.oneshot(name="oneshot1")
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

    def test_auth(self):
        self.auth_result = True
        def dummy_auth():
            return self.auth_result

        checker = failover.oneshot(default_state=failover.ok, auth=dummy_auth)
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
        self.auth_result = True
        def dummy_auth():
            return self.auth_result

        checker = failover.oneshot(default_state=failover.ok, auth=dummy_auth)

        server = create_server()
        start_server(server)

        try:
            server.add_component("oneshot", task=checker, on_post=checker.fire)
            
            con = HTTPConnection(LOOPBACK, server.port)
            con.request("GET", "/oneshot")
            response = con.getresponse()
            self.assertEqual(response.status, OK)

            # Arm the checker -- should get exactly one fail response
            con.request("POST", "/oneshot", "")
            response = con.getresponse()
            self.assertEqual(response.status, OK)

            con.request("GET", "/oneshot")
            response = con.getresponse()
            self.assertEqual(response.status, SERVICE_UNAVAILABLE)
            
            con.request("GET", "/oneshot")
            response = con.getresponse()
            self.assertEqual(response.status, OK)

            # Fail to arm
            self.auth_result = False
            con.request("POST", "/oneshot", "")
            response = con.getresponse()
            self.assertEqual(response.status, UNAUTHORIZED)
        finally:
            stop_server(server)
