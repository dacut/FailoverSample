#!/usr/bin/env python
from __future__ import absolute_import, print_function
from logging import getLogger
from time import time
from .units import count, second, ok
from .validation import validate_after

class Hysteresis(object):
    """
    Hysteresis(task, initial_state=ok, ok_after=count(1), fail_after=count(1),
               name=None)

    Create a Hysteresis object that imposes a delay in the state change of an
    underlying health check task.

    To switch the state from ok to fail, the underlying task must consistently
    fail for the duration specified by fail_after (either a count or time).
    Likewise, to switch the state from fail to ok, the underlying task must
    consistently succeed for the duration specificed by ok_after (count or
    time).

    If the underlying task does meet these criteria, the current state is
    retained.

    Exceptions raised by the underlying task are logged and dropped.  These
    effects are ignored by Hysteresis.
    """
    def __init__(self, task, initial_state=ok, ok_after=count(1),
                 fail_after=count(1), name=None):
        super(Hysteresis, self).__init__()
        self.task = task
        self.current_state = initial_state
        self.ok_after = validate_after(ok_after, "ok_after")
        self.fail_after = validate_after(fail_after, "fail_after")
        self.disagree_count = 0
        self.disagree_start = None
        self.name = name
        return

    def __call__(self):
        log = getLogger("failover.hysteresis")

        log.info("Invoking task %r", self.task)

        try:
            next_state = bool(self.task())
        except Exception as e:
            log.error("Underlying task failed; ignoring this response and "
                      "returning current state %s",
                      ("OK" if self.current_state else "FAIL"),
                      exc_info=True)
            return self.current_state

        if next_state != self.current_state:
            now = time()

            self.disagree_count += 1
            if self.disagree_start is None:
                # Mark the start of the disagreement time.
                self.disagree_start = now

            disagree_time = now - self.disagree_start

            log.info("Disagreement: next state is %s; current state is %s; "
                     "disagree_count is %s; disagree_time is %s",
                     next_state, self.current_state, self.disagree_count,
                     disagree_time)
            
            # Figure out if we need the ok_after or fail_after checks.
            if next_state:
                # Moving from fail to ok
                after = self.ok_after
            else:
                # Moving from ok to fail
                after = self.fail_after

            # Are we doing count-based or time-based?
            if after.unit.canonical() is second:
                disagree = second(disagree_time)
            else:
                disagree = count(self.disagree_count)

            # Have we had enough disagreements?
            if disagree >= after:
                log.info("Disagreement %s exceeds threshold %s; moving to "
                         "new state %s", disagree, after,
                         ("OK" if next_state else "FAIL"))
                # Yep; set the new state.
                self.current_state = next_state
                self.disagree_count = 0
                self.disagree_start = None
            else:
                log.info("Disagreement %s does not exceed threshold %s; "
                         "staying in current state %s", disagree, after,
                         ("OK" if self.current_state else "FAIL"))

        return self.current_state

    def __repr__(self):
        if self.name is not None:
            return self.name
        else:
            return super(Hysteresis, self).__repr__()
# end Hysteresis
