# Failover API #

The public API is entirely available in the `failover` package.

## Server API ##

### Class HealthCheckServer ###

An HTTP server that supports adding health check components.  This is tightly
coupled with the (private) handler class and is derived from
[`BaseHTTPServer.HTTPServer`](https://docs.python.org/2/library/basehttpserver.html).

After creating a `HealthCheckServer` and adding components to it, the
[`serve_forever()`](https://docs.python.org/2/library/socketserver.html#server-objects) method must be invoked to start the server.  It may be stopped by
invoking `shutdown()` from a separate thread.

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

* Returns: `None`
* Throws: `ValueError` if name is invalid


## Health Check Task API ##

### Class TCPCheck ###

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
| `timeout` | The time limit before a connection attempt is abandoned.  This should be a time quantity ([`second`](#type-second), [`minute`](#type-minute), [`hour`](#type-hour), or [`day`](#type-day)); integers and floats are assumed to be seconds.
| `source_host` | If not `None`, the interface to connect from; this must be a hostname, IPv4 address, or IPv6 address (string).
| `source_port` | If not `None`, the port to bind the connecting socket to; this must be an integer in the range 1-65535.
| `name` | If not `None`, the string to return in `repr()` calls.

* Throws: `TypeError` if `host` is not a string; `port` is not a string or
  integer; `timeout` is not a quantity, integer, or float; `source_host` is
  not a string or `None`; or `source_port` is not a string, integer, or
  `None`.
* Throws: `ValueError` if `port` or `service_port` is not a known service
  name or is outside the range 1-65535; or `timeout` is not a time quantity or
  is less than zero.

### Class Hysteresis ###

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
| `fail_after` | If the current state is ok, `task` must fail for this duration before switching to the fail state.  This must be a [`count`](#type-count) quantity or a time quantity ([`second`](#type-second), [`minute`](#type-minute), [`hour`](#type-hour), or [`day`](#type-day)); integers are also accepted and assumed to be counts, but this is not recommended.
| `ok_after` | If the current state is fail, `task` must succeed for this duration before switching to the ok state.  This must be a [`count`](#type-count) quantity or a time quantity ([`second`](#type-second), [`minute`](#type-minute), [`hour`](#type-hour), or [`day`](#type-day)); integers are also accepted and assumed to be counts, but this is not recommended.
| `name` | If not `None`, the string to return in `repr()` calls.

* Throws: `TypeError` if `fail_after` or `ok_after` are not quantities or
  integers.
* Throws: `ValueError` if `fail_after` or `ok_after` are quantities but not
  time or count quantities, or are less than zero.

### Class Background ###

Execute health check tasks asynchronously.

This is used to cache health check results that may be expensive to compute.
For example, an application server may choose to implement checks on each of
its dependencies, taking upwards of a minute to fully execute.  Meanwhile, a
load balancer fronting the server might be hard-wired to query the application
server every 5 seconds; using a `Background` object to proxy these requests will
prevent the server from filling up with health check tasks.

The Background class derives from [`threading.Thread`](https://docs.python.org/2/library/threading.html#thread-objects).

#### Constructor: `Background(task, interval, initial_state=ok, start_thread=True)` ####

Create a new `Background` object to repeatedly invoke a task asynchronously.

Note that `Background` objects will not invoke more than one instance of the
task at a time.

The thread is automatically started unless the `start_thread` parameter is
explicitly set to `False`.

| Parameter | Description
| --------- | -----------
| `task`    | The underlying health check task to call.
| `delay` | The delay between successive calls to `task`.  This must be a time quantity ([`second`](#type-second), [`minute`](#type-minute), [`hour`](#type-hour), or [`day`](#type-day)); integers and floats are assumed to be seconds.  The interval between task executions is the total time to execute the task **plus** this delay.
| `initial_state` | The initial state of the `Background` object (bool).  This is state is only used before the first completion of `task`.
| `start_thread` | Whether the task should be started upon the completion of the constructor.  Subclasses should pass `False` here and invoke `self.start()` themselves to avoid starting the thread before construction has finished.

* Throws: if `delay` is not a quantity, integer, or float.
* Throws: `ValueError` if `delay` is not a time quantity or is less than zero.


#### Method: `stop()` ####

Notifies the background thread to stop running and waits for it to exit.

* Returns: `None`
* Throws: Does not normally throw.

### Class Oneshot ###

A health check task that stays in the given state until fired.  Once fired,
calling the object returns the opposite result exactly once.

This is typically combined with a [`Toggle`](#class-toggle) object to enable manual
failback on a task.

Firing a task can invoke an optional authentication and authorization handler
to verify that the caller has the proper credentials and authority to change
the state.

#### Constructor: `Oneshot(default_state=fail, auth=None, name=None)` ####

Create a new `Oneshot` object.

| Parameter | Description
| --------- | -----------
| `default_state` | The default state to return (bool).
| `auth` | The authentication and authorization handler to invoke when `fire()` is called.  This handler should return `True` or `ok` if the call should proceed; `False` or `fail` otherwise.
| `name` | If not `None`, the string to return in `repr()` calls.

* Throws: Does not normally throw.

#### Method: `fire()` ####

If an authentication and authorization handler has been set, it is invoked.
If it fails, then no action is taken (aside from providing any existing HTTP
handler with a "401 Unauthorized" response) and `False` is returned.

If an authentication and authorization handler has not set or succeeds, this
object becomes armed (i.e. it will return the opposite of `default_state` the
next time it is invoked), any existing HTTP handler is provided a "200 Ok"
response, and `True` is returned.

* Returns: `True` if successfully armed, `False` otherwise.
* Throws: Does not normally throw, but will leak exceptions from the
  authentication and authorization handler.


### Class Toggle ###

A health check that transitions from ok-to-fail or fail-to-ok according to
separate underlying task.

When the object is called and it is currently in the ok state, the `to_fail`
task is called; if it fails, the state changes to fail.  The new state is
returned.

When the object is called and it is currently in the fail state, the `to_ok`
task is called; if it succeeds, the state changes to ok.  The new state is
returned.

This is typically used to implement failover with manual fail-back rules.
For example, `to_fail` will invoke the actual check; once the underlying
service fails, this will stay in the fail state.  The `to_ok` task is a
[`Oneshot`](#class-oneshot) object that is fired by a human.  Only when the
human intervenes and resets the toggle (through an HTTP POST) will the
service failback.

Here's a complete example which checks a mail server (smtp) with a 10 second
timeout, failing after it has been down for 5 minutes and failing back when
an administrator intervenes.
```python
from failover import (
    HealthCheckServer, Hysteresis, minute, Oneshot, TCPCheck, Toggle, second)
server = HealthCheckServer(port=8080)
reset = Oneshot()
server.add_component(
    name="mail",
    task=Toggle(
        initial_state=ok,
        to_fail=Hysteresis(
            task=TCPCheck(host="192.0.2.1", port="smtp", timeout=second(10)),
            fail_after=minute(5),
            ok_after=minute(5)),
        to_ok=reset),
    on_post=reset.fire)
server.serve_forever()
```

#### Constructor: `Toggle(to_fail, to_ok, initial_state=ok, name=None)` ####

Create a new `Toggle` object.
| Parameter | Description
| --------- | -----------
| `to_fail` | The task invoked when in the ok state.  If this task fails, this object transitions to the fail state.
| `to_ok`   | The task invoked when in the fail state.  If this task succeeds, this object transitions to the ok state.
| `initial_state` | The initial state of this toggle object.
| `name` | If not `None`, the string to return in `repr()` calls.

* Throws: Does not normally throw.

## Support Classes ##

### Class ApachePasswdFileCheck ###

Compare the credentials passed in through the HTTP headers against an Apache
`htpasswd` generated file.  (See the [Apache documentation on the `htpasswd`
utility](http://httpd.apache.org/docs/2.2/programs/htpasswd.html) for details
on how to create an `htpasswd` file.)

The [Apache Portable Runtime](https://apr.apache.org/) library must be
installed on the host.  This is typically the case for current Unix-based
systems.

This uses HTTP basic authentication, ***which is insecure over HTTP***.  Use
HTTPS (i.e. HTTP + SSL/TLS) instead.

***This does not currently have protection against XSRF attacks.***

#### Constructor: `ApachePasswdFileCheck(filename)` ####

Create a new password authenticator which, when called, examines the headers
on the current HTTP request against the username and password hash combinations
stored in `filename`.

| Parameter | Description
| --------- | -----------
| `filename` | The name of the file containing the Apache username and password hash combinations (string).  This should be generated and maintained using the [`htpasswd` utility](http://httpd.apache.org/docs/2.2/programs/htpasswd.html).

## Unit Definitions ##

### Type count ###

This is an explicit count unit from the [units](https://pypi.python.org/pypi/units/) library.  It is defined as:
```python
import units
count = units.unit('count')
```

### Type second ###

This is the SI second unit from the [units](https://pypi.python.org/pypi/units/) library.  It is defined as:
```python
import units, units.predefined
units.predefined.define_units()
second = units.unit('s')
```

### Type minute ###

This is a time unit from the [units](https://pypi.python.org/pypi/units/) library, equivalent to 60 seconds.  It is defined as:
```python
import units, units.predefined
units.predefined.define_units()
minute = units.unit('min')
```

### Type hour ###

This is a time unit from the [units](https://pypi.python.org/pypi/units/) library, equivalent to 60 minutes or 3600 seconds.  It is defined as:
```python
import units, units.predefined
units.predefined.define_units()
hour = units.unit('hour')
```

### Type day ###

This is a time unit from the [units](https://pypi.python.org/pypi/units/) library, equivalent to 24 hours or 1440 minutes or 86400 seconds.  It is defined as:
```python
import units, units.predefined
units.predefined.define_units()
day = units.unit('day')
```

### Constant ok ###

Same as `True`.  This provides a self-documenting shortcut in health check
tasks to make the intent explicit.

### Constant fail ###

Same as `False`.  This provides a self-documenting shortcut in health check
tasks to make the intent explicit.
