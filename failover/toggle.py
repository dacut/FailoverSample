#!/usr/bin/env python
from __future__ import absolute_import, print_function
from logging import getLogger
from .units import ok, fail

class Toggle(object):
    def __init__(self, to_fail, to_ok, initial_state=ok, name=None):
        super(Toggle, self).__init__()
        self.to_fail = to_fail
        self.to_ok = to_ok
        self.state = initial_state
        self.name = name
        return

    def __call__(self):
        log = getLogger("failover.toggle")

        task = self.to_fail if self.state else self.to_ok        
        log.info("Current state is %s; invoking task %r",
                 ("OK" if self.state else "FAIL"), task)
        
        try:
            if task():
                self.state = not self.state
                log.info("Task %r returned OK; setting state to %s",
                         task, ("OK" if self.state else "FAIL"))
            else:
                log.info("Task %r returned FAIL; keeping state as %s",
                         task, ("OK" if self.state else "FAIL"))
        except Exception as e:
            log.error("Task %r failed; preserving current state %s",
                      task, ("OK" if self.state else "FAIL"))

        return self.state

    def __repr__(self):
        if self.name is not None:
            return self.name
        else:
            return super(Toggle, self).__repr__()
