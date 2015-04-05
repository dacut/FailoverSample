# FailoverSample
Sample failover scripts for aggregating health checks.

## Examples ##

### Example 1: Simple TCP check ###

Upon receiving a health check request, query a mail server to see if we
can connect within 10 seconds.  Return `OK` if we can, `FAIL` if otherwise.

```python
from failover import *
server = HealthCheckServer(port=8080)
server.add_component(
    "example-1",
    task=TCPCheck(host="192.0.2.1", port=25, timeout=second(10)))
server.run_forever()
```

### Example 2: TCP check with counted hysteresis ###

Start in the `FAIL` state.  Upon receiving a health check request, query a
mail server to see if we can connect within 10 seconds.

*   If we are in the `FAIL` state and the query has been consistently
    healthy the last 5 times, change the state to `OK`.

*   If we are in the `OK` state and the query has been consistently
    unhealthy the last 20 times, change the state to `FAIL`.

```python
from failover import *
server = HealthCheckServer(port=8080)
server.add_component(
    "example-2",
    task=Hysteresis(
        task=TCPCheck(host="192.0.2.1", port=25, timeout=second(10)),
        initial_state=fail,
        ok_after=count(5),
        fail_after=count(20)))
server.run_forever()
```

### Example 3: TCP check with time-based hysteresis ###

Start in the `FAIL` state.  Upon receiving a health check request, query a
mail server to see if we can connect within 10 seconds.

*   If we are in the `FAIL` state and the query has been consistently
    healthy in the last 1 minute, change the state to `OK`.

*   If we are in the `OK` state and the query has been consistently
    unhealthy in the last 2 minutes, change the state to `FAIL`.

```python
from failover import *
server = HealthCheckServer(port=8080)
server.add_component(
    name="example-3",
    task=Hysteresis(
        task=TCPCheck(host="192.0.2.1", port=25, timeout=second(10)),
        initial_state=fail,
        ok_after=minute(1),
        fail_after=minute(2)))
server.run_forever()
```

### Example 4: Asynchronous TCP checks ###

Start in the `FAIL` state.  Every 3 minutes, query a mail server to see if
we can connect within 10 seconds.  Switch states on two consecutive
successes for failures.

When a health check request is received, return the current state without
performing a separate health check.

```python
from failover import *
server = HealthCheckServer(port=8080)
server.add_component(
    name="example-4",
    task=Background(
        task=Hysteresis(
            task=TCPCheck(host="192.0.2.1", port=25, timeout=second(10)),
            initial_state=fail,
            ok_after=count(2),
            fail_after=count(2)),
        interval=minute(3)))
server.run_forever()
```

### Example 5: TCP failover with manual fail-back ###

Start in the `OK` state.  Upon receiving a health check request, query a
mail server to see if we can connect within 10 seconds.  Upon ten consecutive
failures, enter the `FAIL` state.

When in the `FAIL` state, wait for an authorized user to POST a reset request
before switching back to the `OK` state.

```python
from failover import *
server = HealthCheckServer(port=8080)

mail_check = Toggle(
    initial_state=ok,
    to_fail=Hysteresis(
        task=TCPCheck(host="192.0.2.1", port=25, timeout=second(10)),
        initial_state=ok,
        ok_after=count(1),
        fail_after=count(10)),
    to_ok=Oneshot(auth=htpasswd_file("/var/lib/healthcheck_users")))

server.add_component(
    name="mail-u5",
    task=mail_check,
    on_post=mail_check.to_ok.fire)

server.run_forever()
```



 