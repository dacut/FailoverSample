#!/usr/bin/env python
from __future__ import absolute_import, print_function
from logging import getLogger
from six.moves.BaseHTTPServer import BaseHTTPRequestHandler
from six.moves.http_client import (
    INTERNAL_SERVER_ERROR, NOT_FOUND, OK, SERVICE_UNAVAILABLE)
from threading import local

class FailoverRequestHandler(BaseHTTPRequestHandler):
    """
    This handles HTTP requests and acts on them accordingly.  For docs on
    what properties and methods are available, see:
    https://docs.python.org/2/library/basehttpserver.html
    """
    def handle_one_request(self):
        """
        Handle a single HTTP request, setting and clearing the current
        handler before and after handling the request.
        """
        global thread_local
        thread_local.current_handler = self
        try:
            return BaseHTTPRequestHandler.handle_one_request(self)
        finally:
            del thread_local.current_handler

    def do_GET(self):
        """
        Routes a health check request to the appropriate component.
        """
        log = getLogger("failover.get")
        return self.select_and_run_component(self.server.get_handlers, log)

    def do_HEAD(self):
        """
        Routes a health check request to the appropriate component.
        """
        log = getLogger("failover.head")
        return self.select_and_run_component(self.server.get_handlers, log)

    def do_POST(self):
        """
        Routes an update to the appropriate component.
        """
        log = getLogger("failover.get")
        return self.select_and_run_component(self.server.post_handlers, log)

    def select_and_run_component(self, component_map, log):
        """
        Locates a component and executes it.
        """
        # self.path contains the URL path sent to the server.  We route this
        # to a specific function to return an "OK" or "FAIL" response.  To do
        # this, we need to transform /x into x by stripping leading slashes.
        component_name = self.path.lstrip("/")

        log.debug("Converted path %r to component_name %r", self.path,
                  component_name)

        try:
            component = component_map[component_name]
        except KeyError:
            # We don't know about this -- return a 404 (NOT_FOUND) and error
            log.error("Unknown component %s", component_name)
            return self.respond(NOT_FOUND, u"ERROR")

        # Call the specific check function and see whether the component
        # is healthy.
        try:
            log.info("Invoking health check for component %s", component_name)
            if component():
                # Healthy.  Indicate OK.
                log.info("Health check for component %s passed", component_name)
                return self.respond(OK, u"OK")
            else:
                # Unhealthy.  Indicate failure.
                log.info("Health check for component %s failed", component_name)
                return self.respond(SERVICE_UNAVAILABLE, u"FAIL")
        except Exception as e:
            # Health check error
            log.error("Health check for component %s raised an exception",
                      component_name, exc_info=True)
            return self.respond(INTERNAL_SERVER_ERROR, u"ERROR")

    def respond(self, code, message):
        self.send_response(code)

        # All of our responses are plaintext UTF-8
        message = message.encode("utf-8")
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(message)))

        # Always close the connection
        self.send_header("Connection", "close")
        self.end_headers()
        
        # Don't send a response if we have a HEAD request.
        if self.command != "HEAD":
            self.wfile.write(message)
        return
# end FailoverRequestHandler

# Thread-local data; used for storing the current request handler
thread_local = local()

def current_handler():
    """
    Returns the current request handler for this thread.
    """
    global thread_local
    return getattr(thread_local, "current_handler", None)

