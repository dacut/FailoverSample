#!/usr/bin/env python
from __future__ import absolute_import, print_function
from logging import getLogger
from .units import ok, fail
from .validation import validate_duration, validate_hostname, validate_port
import socket

class TCPCheck(object):
    """
    TCPCheck(host, port, timeout, source_host=None, source_port=None)

    Create a TCPCheck object that performs a healthcheck on a TCP service
    when called, returning True if we are able to connect within the
    specified timeout, False otherwise.

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

    def __init__(self, host, port, timeout, source_host=None, source_port=None,
                 name=None):
        super(TCPCheck, self).__init__()
        self.host = validate_hostname(host, "host")
        self.port = validate_port(port, "port")
        self.timeout = validate_duration(timeout, "timeout")
        self.source_host = validate_hostname(source_host, "source_host",
                                             optional=True)
        self.source_port = validate_port(source_port, "source_port",
                                         optional=True)
        self.name = name

        if self.source_host is None:
            self.source_host = ""
        if self.source_port is None:
            self.source_port = 0

        return

    def __call__(self):
        log = getLogger("failover.tcp")
        try:
            log.info("Connecting to %s:%d", self.host, self.port)
            socket.create_connection(
                (self.host, self.port), self.timeout,
                (self.source_host, self.source_port))
            log.info("Connection to %s:%d succeeded", self.host, self.port)
            return ok
        except socket.error as e:
            log.info("Connection to %s:%d failed: %s", self.host, self.port,
                     str(e))
            return fail

    def __repr__(self):
        if self.name is not None:
            return self.name
        else:
            return ("TCPCheck(host=%r, port=%r, timeout=%r, source_host=%r, "
                    "source_port=%r)" % (self.host, self.port, self.timeout,
                                         self.source_host, self.source_port))
