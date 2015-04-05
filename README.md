# FailoverSample
Sample failover scripts for aggregating health checks.

## Examples ##

*   Example 1: Simple TCP IsHealthy

    Upon receiving a health check request, query a mail server to see if we
    can connect within 10 seconds.  Return `OK` if we can, `FAIL` if otherwise.

    ```python
    server = HealthCheckServer(port=8080)
    server.add_component("example-1",
                         task=TCPCheck(host="192.0.2.1", port=25,
                                       timeout=second(10)))
    server.run_forever()
    ```

*   U2: TCP IsHealthy Counted Hysteresis

    Start in the `FAIL` state.  Upon receiving a health check request,
    query a backend TCP service to see if we can connect within a designated
    timeout.

    *   If we are in the `FAIL` state and the query has been consistently
        healthy the last _X_ times, change the state to `OK`.

    *   If we are in the `OK` state and the query has been consistently
        unhealthy the last _Y_ times, change the state to `FAIL`.

    Return the state.

*   U3: TCP IsHealthy Time-Based Hysteresis

    Start in the `FAIL` state.  Upon receiving a health check request,
    query a backend TCP service to see if we can connect within a designated
    timeout.

    *   If we are in the `FAIL` state and the query has been consistently
        healthy the last _X_ seconds, change the state to `OK`.

    *   If we are in the `OK` state and the query has been consistently
        unhealthy the last _Y_ seconds, change the state to `FAIL`.

    Return the state.

*   U4: Asynchronous TCP IsHealthy

    Start in the `FAIL` state.  Every _T_ seconds, query a backend TCP
    service to see if we can connect within a designated timeout.

    *   If we are in the `FAIL` state and the query has been consistently
        healthy the last _X_ seconds, change the state to `OK`.

    *   If we are in the `OK` state and the query has been consistently
        unhealthy the last _Y_ seconds, change the state to `FAIL`.

    Upon receiving a health check request, return the current state.

*   U5: TCP IsHealthy with Manual Reset

    Start in the `OK` state.  Upon receiving a health check request, query
    a backend TCP service to see if we can connect within a designated
    timeout.

    *   If we are in the `OK` state and the query has been consistently
        unhealthy the last _Y_ seconds, change the state to `FAIL`.

    Return the state.

    Upon receiving a reset request, change the state to `OK`.


 