from __future__ import absolute_import, print_function
from failover import ok, Toggle
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
        self.ok_exception = None
        self.fail_exception = None

        def to_ok():
            if self.ok_exception is not None:
                raise self.ok_exception
            return self.is_ok

        def to_fail():
            if self.fail_exception is not None:
                raise self.fail_exception
            return self.is_fail

        toggle = Toggle(to_ok=to_ok, to_fail=to_fail, initial_state=ok)

        # Don't transition without a toggle.
        self.assertTrue(toggle())
        self.assertTrue(toggle())

        # Don't transition if to_fail raises an exception
        self.fail_exception = ValueError()
        self.assertTrue(toggle())
        self.fail_exception = None

        # Goto the fail state.
        self.is_fail = True
        self.assertFalse(toggle())
        self.assertFalse(toggle())

        # Don't transition yet.
        self.is_fail = False
        self.assertFalse(toggle())

        # Don't transition if to_ok raises an exception
        self.ok_exception = ValueError()
        self.assertFalse(toggle())
        self.ok_exception = None
        
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

        # Check the name
        self.assertTrue(repr(toggle).startswith("<failover.toggle.Toggle"))
        toggle.name = "toggle1"
        self.assertEqual(repr(toggle), "toggle1")

        return
