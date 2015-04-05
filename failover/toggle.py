#!/usr/bin/env python
from __future__ import absolute_import, print_function
from logging import getLogger
from .units import ok, fail

class Toggle(object):
    """
    Toggle(to_fail, to_ok, initial_state=ok, name=None)

    Create a Toggle object that transitions from ok-to-fail or fail-to-ok
    according to an underlying task.

    When the object is called and it is currently in the ok state, the to_fail
    task is called; if it fails, the state changes to fail.  The new state
    is returned.

    When the object is called and it is currently in the fail state, the to_ok
    task is called; if it succeeds, the state changes to ok.  The new state is
    returned.

    This is typically used to implement failover with manual fail-back rules.
    For example, to_fail will invoke the actual check; to_ok will be a Oneshot
    object.  When the to_fail task fails, the state will change to fail.  Only
    when the Oneshot object is fired will this task then change back to ok.
    """
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
        toggle_result = not self.state
        log.info("Current state is %s; invoking task %r",
                 ("OK" if self.state else "FAIL"), task)
        
        try:
            task_result = bool(task())

            if task_result == toggle_result:
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
