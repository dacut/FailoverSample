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

