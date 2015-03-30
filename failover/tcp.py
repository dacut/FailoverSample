#!/usr/bin/env python
from __future__ import absolute_import, print_function
from logging import getLogger
from .units import ok, fail
from .validation import validate_duration, validate_hostname, validate_port
import socket

def check_tcp_service(host, port, timeout, source_host=None, source_port=None):
    """
    check_tcp_service(host, port, timeout, source_host=None, source_port=None)
      -> function() -> bool

    Create a function that performs a healthcheck on a TCP service when called,
    returning True if we are able to connect within the specified timeout,
    False otherwise.

    Timeout should be specified with a given unit, e.g.:
        from failover import check_tcp_service, second
        check_tcp_service(('1.2.3.4', 25), second(15))
    If units are not specified, seconds are assumed.

    Host can be an IPv4 address, IPv6 address, or DNS hostname.

    Port can be an integer port number of a service name.

    If source_host is not None, the specified interface is used for outgoing
    traffic to the host.

    If source_port is not None, the specified port is used for outgoing
    traffic to the host.
    """
    import socket

    host = validate_hostname(host, "host")
    port = validate_port(port, "port")
    timeout = validate_duration(timeout, "timeout")
    source_host = validate_hostname(source_host, "source_host", optional=True)
    source_port = validate_port(source_port, "source_port", optional=True)

    if source_host is None:
        source_host = ""
    if source_port is None:
        source_port = 0

    log = getLogger("failover.tcp")

    def check_function():
        import socket
        try:
            log.info("Connecting to %s:%d", host, port)
            socket.create_connection(
                (host, port), timeout, (source_host, source_port))
            log.info("Connection to %s:%d succeeded", host, port)
            return ok
        except socket.error as e:
            log.info("Connection to %s:%d failed: %s", host, port, str(e))
            return fail

    return check_function

