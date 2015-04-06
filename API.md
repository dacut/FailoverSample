# Failover API #

The public API is entirely available in the `failover` package.

## Server API ##

### `HealthCheckServer` ###

An HTTP server that supports adding health check components.  This is tightly
coupled with the (private) handler class.

#### Constructor: `HealthCheckServer(port, host="")` ####

Create a new `HealthCheckServer` listenting on the specified port (and
interface, if desired).

#### Method: `add_component(name, task, on_post=None)` ####

Add a health check task.  `name` (string) is the relative URL path to mount
the task onto the HTTP server; it must not have leading slashes ('/').
`task` is a callable object invoked on GET or HEAD requests.  It must
return a boolean value (or a value convertible to a Python `bool`), with
`True` indicating the health check passed, `False` indicating that it failed.
Use (`ok`)[#ok] and (`fail`)[#fail] as self-documenting shortcuts to avoid
the mental overhead on this convention.

If not `None`, `on_post` is a callable to execute on POST requests.

## Health Check Task API ##

### `TCPCheck` ###

A health check task that checks whether a TCP service is accepting
connections.

#### Constructor: `TCPCheck(host, port, timeout, source_host=None, source_port=None, name=None)` ####

Create a new `TCPCheck` instance that connects to the specified `host`
(string hostname or IPv4/IPv6 address) and `port` (string servicename or
integer port number from 1-65535) combination.  The check succeeds if the
server accepts the connection within `timeout` (a time unit quantity or
integer/float number of seconds).

| Parameter | Description
| --------- | -----------
| `host`    | The hostname, IPv4 address, or IPv6 address of the host to test (string).
| `port`    | The servicename (string) or TCP port (integer, 1-65535) to test.
| `timeout` | The time limit before a connection attempt is abandoned.  This should be a time quantity ([`second`](#second), [`minute`](#minute), [`hour`](#hour), or [`day`](#day)); integers and floats are assumed to be seconds.
| `source_host` | If not `None`, the interface to connect from; this must be a hostname, IPv4 address, or IPv6 address (string).
| `source_port` | If not `None`, the port to bind the connecting socket to; this must be an integer in the range 1-65535.
| `name` | If not `None`, the string to return in `repr()` calls.

### `Hysteresis` ###

A health check task that adds hysteresis around another health check task.

Real world systems are imperfect, and distributed systems are examples of
this.  A TCP health check may fail even though the system being tested is
up and reachable for myriad reasons: network congestion, packet loss,
excessive load on the monitoring system, etc.  Many failovers affect the
user experience negatively since sessions often must be reestablished.
Therefore, it is desirable to failover only when the issue is non-transient.

Of course, determining whether an issue is transient or not is typically
impossible.  Hysteresis is often used as a heuristic for making this
determination:  a failover/failback action is taken only when the
underlying health check has been seen to consistently fail/pass beyond a set
duration (either in time or number of checks).

#### Constructor: `Hysteresis(task, initial_state=ok, ok_after=count(1), fail_after=count(1), name=None)` ####

Create a `Hysteresis` object that imposes a delay in the state change of the
underlying health check task given by the `task` parameter.

| Parameter | Description
| --------- | -----------
| `task`    | The underlying health check task to call.
| `initial_state` | The initial state of the `Hysteresis` object (bool).
| `fail_after` | If the current state is ok, `task` must fail for this duration before switching to the fail state.  This must be a [`count`](#count) quantity or a time quantity ([`second`](#second), [`minute`](#minute), [`hour`](#hour), or [`day`](#day)); integers are also accepted and assumed to be counts, but this is not recommended.
| `ok_after` | If the current state is fail, `task` must succeed for this duration before switching to the ok state.  This must be a [`count`](#count) quantity or a time quantity ([`second`](#second), [`minute`](#minute), [`hour`](#hour), or [`day`](#day)); integers are also accepted and assumed to be counts, but this is not recommended.
| `name` | If not `None`, the string to return in `repr()` calls.

## Unit Definitions ##

### `count` ###

This is an explicit count unit from the [units](https://pypi.python.org/pypi/units/) library.  It is defined as:
```python
import units
count = units.unit('count')
```

### `second` ###

This is the SI second unit from the [units](https://pypi.python.org/pypi/units/) library.  It is defined as:
```python
import units, units.predefined
units.predefined.define_units()
second = units.unit('s')
```

### `minute` ###

This is a time unit from the [units](https://pypi.python.org/pypi/units/) library, equivalent to 60 seconds.  It is defined as:
```python
import units, units.predefined
units.predefined.define_units()
minute = units.unit('min')
```

### `hour` ###

This is a time unit from the [units](https://pypi.python.org/pypi/units/) library, equivalent to 60 minutes or 3600 seconds.  It is defined as:
```python
import units, units.predefined
units.predefined.define_units()
hour = units.unit('hour')
```

### `day` ###

This is a time unit from the [units](https://pypi.python.org/pypi/units/) library, equivalent to 24 hours or 1440 minutes or 86400 seconds.  It is defined as:
```python
import units, units.predefined
units.predefined.define_units()
day = units.unit('day')
```

### `ok` ###

Same as `True`.  This provides a self-documenting shortcut in health check
tasks to make the intent explicit.

### `fail` ###

Same as `False`.  This provides a self-documenting shortcut in health check
tasks to make the intent explicit.
