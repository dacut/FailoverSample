from __future__ import absolute_import, print_function
import failover
import logging
from sys import stderr
from unittest import TestCase, main

LOOPBACK = "127.0.0.1"

class ToggleTest(TestCase):
    def setUp(self):
        logging.basicConfig(
            stream=stderr, level=logging.DEBUG,
            format=("%(asctime)s %(module)s [%(levelname)s] "
                    "%(filename)s:%(lineno)d: %(message)s"))

    def test_toggle(self):
        self.is_ok = False
        self.is_fail = False

        def to_ok():
            return self.is_ok
        def to_fail():
            return self.is_fail

        toggle = failover.toggle(to_ok=to_ok, to_fail=to_fail,
                                 initial_state=failover.ok)

        # Don't transition without a toggle.
        self.assertTrue(toggle())
        self.assertTrue(toggle())

        # Goto the fail state.
        self.is_fail = True
        self.assertFalse(toggle())
        self.assertFalse(toggle())

        # Don't transition yet.
        self.is_fail = False
        self.assertFalse(toggle())
        
        # Transition back now.
        self.is_ok = True
        self.assertTrue(toggle())
        self.assertTrue(toggle())

        # No transition again
        self.is_ok = False
        self.assertTrue(toggle())
        self.assertTrue(toggle())

        # Flip flop transitions.
        self.is_ok = self.is_fail = True
        self.assertFalse(toggle())
        self.assertTrue(toggle())
        self.assertFalse(toggle())
        self.assertTrue(toggle())

        return
