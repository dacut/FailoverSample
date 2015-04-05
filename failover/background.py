#!/usr/bin/env python
from __future__ import absolute_import, print_function
from logging import getLogger
from .units import ok
from .validation import validate_duration
from threading import Condition, Thread

log = getLogger("failover.background")

class Background(Thread):
    """
    Background(task, interval, start=ok)

    Create a Background object that invokes an underlying health check task
    asynchronously and saves the state.

    This is used to cache health check results that may be expensive to
    compute.  For example, an application server may choose to implement checks
    on each of its dependencies, taking upwards of a minute to fully execute.
    Meanwhile, a load balancer fronting the server might be hard-wired to query
    the application server every 5 seconds; using a Background object to proxy
    these requests will prevent the server from filling up with health check
    tasks.
    """
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

