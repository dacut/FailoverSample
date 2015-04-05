#!/usr/bin/env python
from __future__ import absolute_import, print_function
import socket
from types import NoneType
from .units import count, second
from units.quantity import Quantity

def validate_hostname(hostname, parameter_name="host", optional=False):
    """
    validate_hostname(hostname, parameter_name="host", optional=False) -> str

    Verify a given string contains a valid hostname or IPv4/IPv6 address.  An
    exception is raised (naming the offending parameter via parameter_name) if
    the string is not a valid hostname or IP address.

    If optional is True, hostname can also be None.
    """
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
    """
    validate_port(port, parameter_name="port", optional=False) -> int

    Verify a given parameter is a valid port; this must be an integer in the
    range 1-65535 (inclusive) or a string containing a valid TCP service name
    (from /etc/services).  If this is not the case, an exception is raised
    (naming the offending parameter via parameter_name).

    If a service name was passed in, the return value is the equivalent
    integer TCP port.

    If optional is True, port can also be None.
    """
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
    """
    validate_duration(duration, parameter_name="duration") -> float

    Verify a given parameter is a valid duration; this must be a non-negative
    number (int or float) or, preferably, a time quantity from the units
    library (see failover.units).  If the parameter is not valid, an exception
    is raised (naming the offending parameter via parameter_name).
    
    The return value is a float indicating the duration in seconds.
    """
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

    return float(duration)

def validate_after(after, parameter_name="after"):
    """
    validate_after(after, parameter_name="after") -> second/count

    Verify a given parameter is a valid event; this must be a positive count
    (int or failover.units.count quantity) or a positive time unit (see
    failover.units).  If the parameter is not valid, an exception is raised
    (naming the offending parameter via parameter_name).

    The return value is a quantity with either second or count units.
    """
    errmsg = (parameter_name + " must be a positive time or count unit, "
              "or positive integer count")
    if isinstance(after, Quantity):
        after_unit = after.unit.canonical()

        if after_unit is count:
            # Don't do anything to the value
            if after.num <= 0:
                raise ValueError(errmsg)
        elif after_unit is second:
            # Convert the value to seconds
            if after.num <= 0:
                raise ValueError(errmsg)
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

