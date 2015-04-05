# Failover API #

The public API is entirely available in the `failover` package.

## `HealthCheckServer` ##

An HTTP server that supports adding health check components.  This is tightly
coupled with the (private) handler class.

### Constructor: `HealthCheckServer(port, host="")` ###
