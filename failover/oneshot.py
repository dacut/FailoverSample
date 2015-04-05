#!/usr/bin/env python
from __future__ import absolute_import, print_function
from .handler import current_handler
from logging import getLogger
from six.moves.http_client import UNAUTHORIZED, OK
from .units import ok, fail

class Oneshot(object):
    """
    Oneshot(default_state=fail, auth=None, name=None)

    Create a Oneshot object that stays in the given state until fired.  Once
    fired, calling the object returns the opposite result exactly once.

    When fired, the auth check is invoked.  This can be used to verify
    credentials passed to an HTTP handler, for example.

    This is typically combined with a Toggle object to enable manual reset
    on a task.
    """
    def __init__(self, default_state=fail, auth=None, name=None):
        super(Oneshot, self).__init__()
        self.default_state = default_state
        self.next_state = default_state
        self.auth = auth
        self.name = name
        return

    def __call__(self):
        result = self.next_state
        self.next_state = self.default_state
        return result

    def fire(self):
        """
        oneshot.fire() -> bool

        If auth has been set, it is invoked.  If it fails, then no action is
        taken (except providing any existing HTTP handler with a
        "401 Unauthorized" response) and False is returned.

        If auth is not set or succeeds, this object becomes armed (i.e. will
        return the opposite of default_state the next time it is invoked),
        any existing HTTP handler is provided a "200 Ok" response, and True is
        returned.
        """
        handler = current_handler()
        if self.auth is not None and not self.auth():
            if handler is not None:
                handler.respond(UNAUTHORIZED, "Invalid credentials")
            return False

        self.next_state = not self.default_state
        if handler is not None:
            handler.respond(OK, "Armed")
        return True

    def __repr__(self):
        if self.name is not None:
            return self.name
        else:
            return super(Oneshot, self).__repr__()

