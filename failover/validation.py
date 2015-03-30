#!/usr/bin/env python
from __future__ import absolute_import, print_function
import socket
from types import NoneType
from .units import count, second
from units.quantity import Quantity

def validate_hostname(hostname, parameter_name="host", optional=False):
    errmsg = (parameter_name + " must be a string containing a valid hostname")

    if optional:
        errmsg += ", IPv4 or IPv6 address, or None"
    else:
        errmsg += " or IPv4 or IPv6 address"

    if not (isinstance(hostname, basestring) or
            (optional and isinstance(hostname, NoneType))):
        raise TypeError(errmsg)

    # XXX: Put host through a regex?
    
    return hostname

def validate_port(port, parameter_name="port", optional=False):
    errmsg = (parameter_name + " must be an integer port number from "
              "1-65535 (inclusive)")

    if optional:
        errmsg += ", a string service name, or None"
    else:
        errmsg += "or a string service name"

    if isinstance(port, int):
        if port <= 0 or port > 65535:
            raise ValueError(errmsg)
    elif isinstance(port, basestring):
        try:
            port = socket.getservbyname(port, "tcp")
        except socket.error:
            raise ValueError("Unknown service name %r" % port)
    elif not (optional and isinstance(port, NoneType)):
        raise TypeError(errmsg)

    return port

def validate_duration(duration, parameter_name="duration"):
    errmsg = (parameter_name + " must be a non-negative time unit or numeric "
              "value in seconds: %r")
    if isinstance(duration, Quantity):
        duration = duration / second(1.0)
        if not isinstance(duration, (int, long, float)) or duration < 0:
            raise ValueError(errmsg % (duration,))
    elif isinstance(duration, (int, long, float)):
        if duration < 0:
            raise ValueError(errmsg % (duration,))
    else:
        raise TypeError(errmsg % (duration,))

    return duration

def validate_after(after, parameter_name="after"):
    errmsg = (parameter_name + " must be a positive time or count unit, "
              "or positive integer count")
    if isinstance(after, Quantity):
        after_unit = after.unit.canonical()

        if after_unit is count:
            # Don't do anything to the value
            pass
        elif after_unit is second:
            # Convert the value to seconds
            after = second(0) + after
        else:
            raise ValueError(errmsg)
    elif isinstance(after, (int, long)):
        if after <= 0:
            raise ValueError(errmsg)
        after = count(after)
    else:
        raise TypeError(errmsg)

    return after

