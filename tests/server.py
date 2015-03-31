from __future__ import absolute_import, print_function
import failover
from random import SystemRandom
from threading import Thread, Condition

LOOPBACK = "127.0.0.1"

def get_test_port():
    while True:
        port = SystemRandom().randint(1025, 32767)
        # Make sure we can't connect to this port.
        try:
            con = create_connection(LOCALHOST, port)
            con.close()
            # We connected; try another port
        except:
            break
    return port

def create_server(port=None):
    if port is None:
        port = get_test_port()
    
    server = failover.create_healthcheck_server(port)
    server.port = port
    return server

def start_server(server):
    server_thread = Thread(target=server.serve_forever)
    server_thread.start()
    server.thread = server_thread
    return server

def stop_server(server):
    server.shutdown()
    server.thread.join()
