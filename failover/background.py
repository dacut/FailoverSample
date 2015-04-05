#!/usr/bin/env python
from __future__ import absolute_import, print_function
from logging import getLogger
from .units import ok
from .validation import validate_duration
from threading import Condition, Thread

log = getLogger("failover.background")

class Background(Thread):
    def __init__(self, task, interval, start=ok):
        super(Background, self).__init__()
        self.task = task
        self.state = start
        self.interval = validate_duration(interval, "interval")
        self.lock = Condition()
        self.exit_requested = False
        self.start()
        return

    def run(self):
        with self.lock:
            while not self.exit_requested:
                # Allow another thread to request this thread to stop.
                self.lock.wait(self.interval)
                if self.exit_requested:
                    break

                try:
                    self.state = self.task()
                except Exception as e:
                    log.error("Failed to execute background task: %s", e,
                              exc_info=True)
        return

    def __call__(self):
        return self.state

    def stop(self):
        with self.lock:
            self.exit_requested = True
            self.lock.notify()

        self.join()
        return

