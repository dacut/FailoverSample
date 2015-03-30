#!/usr/bin/env python
from __future__ import absolute_import, print_function
from six.moves.BaseHTTPServer import HTTPServer

class FailoverServer(HTTPServer):
    def __init__(self, server_address):
        # Create a function which instantiates the handler with a link back
        # to this server.
        def create_handler(*args, **kw):
            from .handler import FailoverRequestHandler
            handler = FailoverRequestHandler(*args, **kw)
            handler.server = self
            return handler

        HTTPServer.__init__(self, server_address, handler)
        self.get_handlers = {}
        self.post_handlers = {}
        return
    
    def add_component(self, name, task, on_post=None):
        if task:
            self.get_handlers[name] = task

        if on_post:
            self.post_handlers[name] = on_post
        return

def create_healthcheck_server(port, host=None):
    """
    create_healthcheck_server(port) -> HealthcheckServer

    Creates a new health check server listening on the specified TCP port.
    """

    # Create a wrapper which instantiates a FailoverRequestHandler with the
    # correct component_map.
    component_map = {}
    def new_handler(*args, **kw):
        return FailoverRequestHandler(component_map, *args, **kw)
    
    return HTTPServer((host, port), new_handler)