from __future__ import absolute_import, print_function
import failover
import logging
from sys import stderr
from time import sleep
from unittest import TestCase, main

class TestTask(object):
    def __init__(self, result=failover.ok):
        super(TestTask, self).__init__()
        self.result = result
        self.exception = None
        return

    def __call__(self):
        if self.exception:
            raise self.exception
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

    def test_timed_hysteresis(self):
        test_task = TestTask()
        checker = failover.hysteresis(
            task=test_task, start=failover.ok,
            ok_after=failover.second(0.3),
            fail_after=failover.second(0.5))

        self.assertTrue(checker())
        self.assertTrue(checker())

        test_task.result = failover.fail
        self.assertTrue(checker())      # Failure -- need a 0.5 sec delay
        self.assertTrue(checker())      # Failure -- no delay, still ok
        sleep(0.5)
        self.assertFalse(checker())     # Failure -- delayed, so now failed
        self.assertFalse(checker())
        
        test_task.result = failover.ok
        self.assertFalse(checker())     # Success -- need a 0.3 sec delay
        self.assertFalse(checker())     # Success -- no delay, still failed
        sleep(0.3)
        self.assertTrue(checker())      # Success -- delayed, so now ok
        self.assertTrue(checker())
        return

    def test_failed_hysteresis(self):
        test_task = TestTask()
        checker = failover.hysteresis(
            task=test_task, start=failover.ok,
            ok_after=failover.count(2),
            fail_after=failover.count(2))

        self.assertTrue(checker())
        # Throw an exception from the underlying task; hysteresis should still
        # succeed
        test_task.exception = ValueError()
        self.assertTrue(checker())
        self.assertTrue(checker())
        self.assertTrue(checker())
        self.assertTrue(checker())

        # Start failing
        test_task.exception = None
        test_task.result = failover.fail
        self.assertTrue(checker())
        self.assertFalse(checker())
        self.assertFalse(checker())
        self.assertFalse(checker())

        # Throw an exception from the underlying task; hysteresis should still
        # fail.
        test_task.exception = ValueError()
        self.assertFalse(checker())
        self.assertFalse(checker())
        self.assertFalse(checker())
        self.assertFalse(checker())

        
