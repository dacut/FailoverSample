#!/usr/bin/env python
from __future__ import absolute_import, print_function
from six.moves.BaseHTTPServer import HTTPServer

class HealthCheckServer(HTTPServer):
    """
    HealthCheckServer(port, host="")

    Create a HealthCheckServer (an HTTP server) listening on the given port
    (and interface, if specified).
    """
    def __init__(self, port, host=""):
        # Create a function which instantiates the handler with a link back
        # to this server.
        def create_handler(*args, **kw):
            from .handler import FailoverRequestHandler
            handler = FailoverRequestHandler(*args, **kw)
            handler.server = self
            return handler

        HTTPServer.__init__(self, (host, port), create_handler)
        self.get_handlers = {}
        self.post_handlers = {}
        return
    
    def add_component(self, name, task, on_post=None):
        """
        hcs.add_component(name, task, on_post=None)

        Add the specified health check task at the specified path name.
        name must be a string without leading slashes.  task must be a callable
        object.

        If on_post is specified, it specifies an alternate handler to invoke
        on POST requests.
        """

        if name.startswith("/"):
            raise ValueError("name cannot start with a slash")

        if getattr(task, "name", None) is None:
            try:
                task.name = name
            except Exception as e:
                pass

        if task:
            self.get_handlers[name] = task

        if on_post:
            self.post_handlers[name] = on_post
        return
