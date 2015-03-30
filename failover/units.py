#!/usr/bin/env python
from __future__ import absolute_import, print_function
import units, units.predefined

"""
Units used for time and counts.
"""

# Make sure base SI units are defined.
units.predefined.define_units()
second = units.unit('s')
minute = units.unit('min')
hour = units.unit('hour')
day = units.unit('day')
count = units.unit('count')

# Mapping boolean results to OK/Failure -- this can be a bit ambiguous since
# we expect "health_check()" to be true if the service is healthy (the
# convention we follow), yet the exit code for success on Unix is 0.
ok = True
fail = False
