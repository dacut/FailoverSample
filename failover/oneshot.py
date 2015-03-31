#!/usr/bin/env python
from __future__ import absolute_import, print_function
from .handler import current_handler
from logging import getLogger
from six.moves.http_client import UNAUTHORIZED, OK
from .units import ok, fail

class Oneshot(object):
    def __init__(self, default_state=fail, auth=None):
        super(Oneshot, self).__init__()
        self.default_state = default_state
        self.next_state = default_state
        self.auth = auth
        return

    def __call__(self):
        result = self.next_state
        self.next_state = self.default_state
        return result

    def fire(self):
        handler = current_handler()
        if self.auth is not None and not self.auth():
            if handler is not None:
                handler.respond(UNAUTHORIZED, "Invalid credentials")
            return False

        self.next_state = not self.default_state
        if handler is not None:
            handler.respond(OK, "Armed")
        return True

def oneshot(default_state=fail, auth=None):
    return Oneshot(default_state=default_state, auth=auth)
