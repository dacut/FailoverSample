from __future__ import absolute_import, print_function
import failover
import logging
from sys import stderr
from time import sleep
from unittest import TestCase, main

class BackgroundTask(object):
    def __init__(self, state=failover.ok):
        super(BackgroundTask, self).__init__()
        self.state = state
        self.exception = None
        self.n_calls = 0
        return

    def __call__(self):
        self.n_calls += 1
        if self.exception:
            raise self.exception
        return self.state

class BackgroundTest(TestCase):
    def setUp(self):
        logging.basicConfig(
            stream=stderr, level=logging.DEBUG,
            format=("%(asctime)s %(module)s [%(levelname)s] "
                    "%(filename)s:%(lineno)d: %(message)s"))

    def test_background(self):
        task = BackgroundTask()
        checker = failover.background(
            task=task, interval=failover.second(0.1))

        # Check function should be called even if no other activity is
        # occurring
        sleep(0.31)
        self.assertEqual(task.n_calls, 3)
        
        self.assertTrue(checker())

        # If the checker starts failing, we should not see the result instantly
        task.state = failover.fail
        self.assertTrue(checker())

        # But if we sleep, it should then fail
        sleep(0.2)
        self.assertFalse(checker())

        checker.stop()
        return

    def test_exception(self):
        task = BackgroundTask()
        checker = failover.background(
            task=task, interval=failover.second(0.1))

        sleep(0.11)
        self.assertTrue(checker())

        # If the task throws an exception, it should not affect the result.
        task.exception = ValueError()
        self.assertTrue(checker())
        sleep(0.15)
        self.assertTrue(checker())

        checker.stop()
        return

        
