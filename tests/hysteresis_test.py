from __future__ import absolute_import, print_function
import failover
import logging
from sys import stderr
from unittest import TestCase, main

class TestTask(object):
    def __init__(self, result=failover.ok):
        super(TestTask, self).__init__()
        self.result = result
        return

    def __call__(self):
        return self.result

class HysteresisTest(TestCase):
    def setUp(self):
        logging.basicConfig(
            stream=stderr, level=logging.DEBUG,
            format=("%(asctime)s %(module)s [%(levelname)s] "
                    "%(filename)s:%(lineno)d: %(message)s"))

    def test_counted_hysteresis(self):
        test_task = TestTask()
        checker = failover.hysteresis(
            task=test_task, start=failover.ok,
            ok_after=failover.count(5),
            fail_after=failover.count(3))

        self.assertTrue(checker())
        self.assertTrue(checker())

        test_task.result = failover.fail
        self.assertTrue(checker())      # First failure -- still ok
        self.assertTrue(checker())      # Second failure -- still ok
        self.assertFalse(checker())     # Third failure -- transition
        self.assertFalse(checker())
        
        test_task.result = failover.ok
        self.assertFalse(checker())     # First success -- still failed
        self.assertFalse(checker())     # Second success -- still failed
        self.assertFalse(checker())     # Third success -- still failed
        self.assertFalse(checker())     # Fourth success -- still failed
        self.assertTrue(checker())      # Fifth success -- transition
        self.assertTrue(checker())

        return
