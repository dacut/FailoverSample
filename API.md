# Failover API #

The public API is entirely available in the `failover` package.

## `HealthCheckServer` ##

An HTTP server that supports adding health check components.  This is tightly
coupled with the (private) handler class.

### Constructor: `HealthCheckServer(port, host="")` ###

Create a new `HealthCheckServer` listenting on the specified port (and
interface, if desired).

### Method: `add_component(name, task, on_post=None)` ###

Add a health check task.  `name` (string) is the relative URL path to mount
the task onto the HTTP server; it must not have leading slashes ('/').
`task` is a callable object invoked on GET or HEAD requests.  It must
return a boolean value (or a value convertible to a Python `bool`), with
`True` indicating the health check passed, `False` indicating that it failed.
Use `failover.units.ok` and `failover.units.fail` as self-documenting
shortcuts to avoid the mental overhead on this convention.

If not `None`, `on_post` is a callable to execute on POST requests.

## `TCPCheck` ##

A health check task that checks whether a TCP service is accepting
connections.

### Constructor: `TCPCheck(host, port, timeout, source_host=None, source_port=None, name=None)` ###

Create a new `TCPCheck` instance that connects to the specified `host`
(string hostname or IPv4/IPv6 address) and `port` (string servicename or
integer port number from 1-65535) combination.  The check succeeds if the
server accepts the connection within `timeout` (a time unit quantity or
integer/float number of seconds).

If `source_host` is not `None`, it must be a string hostname or IPv4/IPv6
address indicating the interface to connect from.  If `source_port` is not
`None`, it must be a string servicename or integer port number from 1-65535
to bind the connecting socket to.

If `name` is not `None`, it is used when `repr()` is called on the object.

| Parameter | Description
| --------- | -----------
| `host`    | The hostname, IPv4 address, or IPv6 address of the host to test (string).
| `port`    | The servicename (string) or TCP port (integer, 1-65535) to test.
| `timeout` | The time limit before a connection attempt is abandoned.  This should be a time quantity (see [`second`](#second)); integers and floats are assumed to be seconds.
| `source_host` | \[Default: `None`\] The interface to connect from; this must be a hostname, IPv4 address, or IPv6 address (string).
| `source_port` | \[Default: `None`\] The port to bind the connecting socket to; this must be an integer in the range 1-65535.

## `Hysteresis` ##

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

### Constructor: `Hysteresis(task, initial_state=ok, ok_after=count(1), fail_after=count(1), name=None)` ###

Create a `Hysteresis` object that imposes a delay in the state change of the
underlying health check task given by the `task` parameter.

To switch the state from ok to fail, the underlying task must consistently
fail for the duration specified by `fail_after` (either a count or time
quantity; integers are assumed to be counts).