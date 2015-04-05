from __future__ import absolute_import, print_function
import failover
import logging
from select import select
from six.moves.http_client import (
    HTTPConnection, INTERNAL_SERVER_ERROR, NOT_FOUND, OK, SERVICE_UNAVAILABLE)
from socket import (
    AF_INET, create_connection, INADDR_ANY, SOCK_STREAM, socket, SOL_SOCKET,
    SO_REUSEADDR)
from sys import stderr
from threading import Thread, Condition
from time import sleep
from unittest import TestCase, main

from .server import create_server, start_server, stop_server

LOOPBACK = "127.0.0.1"
UNROUTABLE = "192.0.2.1" # RFC 5737 -- TEST-NET-1 space, unroutable globally

log = logging.getLogger("test.tcp")

class TCPService(Thread):
    def __init__(self, *args, **kw):
        super(TCPService, self).__init__(*args, **kw)
        self.lock = Condition()
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.socket.bind((LOOPBACK, 0))
        self.socket.listen(5)
        self.port = self.socket.getsockname()[1]
        self.timeout = 0.1
        self.exit_requested = False
        log.info("Created server on port %d", self.port)
        return

    def close(self):
        log.info("Closing server on port %d", self.port)
        with self.lock:
            if self.socket is not None:
                self.socket.close()
                self.socket = None
            self.lock.notify()
        return

    def listen(self):
        log.info("Activating server on port %d", self.port)
        with self.lock:
            if self.socket is None:
                self.socket = socket(AF_INET, SOCK_STREAM)
                self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                self.socket.bind((LOOPBACK, self.port))
                self.socket.listen(5)
            self.lock.notify()

        return

    def run(self):
        import time

        my_sleep = time.sleep
        self.lock.acquire()
        
        try:
            while not self.exit_requested:
                log.debug("Allowing other thread to signal us")
                try:
                    self.lock.wait(0.1)
                except RuntimeError:
                    pass

                if self.socket:
                    log.debug("Waiting for connection")
                    result = select([self.socket], [], [], self.timeout)
                    if result[0]:
                        log.debug("Healthy -- received connection")
                        conn, client = self.socket.accept()
                        log.debug("discarding data from %s:%d", client[0], client[1])
                        self.discard(conn)
                    else:
                        log.debug("Healthy -- no connection")
                else:
                    self.lock.release()
                    try:
                        log.debug("Unhealthy -- ignoring connection")
                        my_sleep(self.timeout)
                    finally:
                        self.lock.acquire()
        except Exception as e:
            log.error("YIKES", exc_info=True)
        finally:
            self.lock.release()

        log.debug("Exiting")

        return

    def discard(self, connection):
        """
        Read and discard all received data on a connection.
        """
        def do_discard():
            while True:
                data = connection.recv(1024)
                if len(data) == 0:
                    connection.close()
                    break
        thread = Thread(target=do_discard)
        thread.start()
        return
        
class CheckTCPServiceTest(TestCase):
    def start_service(self):
        service = TCPService()
        service.start()
        return service

    def setUp(self):
        logging.basicConfig(
            stream=stderr, level=logging.DEBUG,
            format=("%(asctime)s %(module)s [%(levelname)s] "
                    "%(filename)s:%(lineno)d: %(message)s"))

    def test_basic_connection(self):
        service = self.start_service()
        checker = failover.TCPCheck(
            LOOPBACK, service.port, failover.second(10), name="tcp1")
        
        self.assertTrue(checker())
        service.close()
        self.assertFalse(checker())
        service.listen()
        self.assertTrue(checker())
        self.assertTrue(checker())

        # Check repr
        self.assertEqual(repr(checker), "tcp1")
        checker.name = None
        self.assertTrue(repr(checker).startswith(
            "TCPCheck(host='127.0.0.1', port=%d, timeout=" % service.port))
        
        service.exit_requested = True
        service.join()
        return

    def test_unroutable(self):
        checker = failover.TCPCheck(
            UNROUTABLE, 80, failover.second(0.1))

        self.assertFalse(checker())
        return

    def test_server(self):
        service = self.start_service()
        server = create_server()

        # Make sure we reject invalid component names
        try:
            server.add_component('/foo', None)
            self.fail("Expected ValueError")
        except ValueError:
            pass

        server.add_component(
            'always-succeed',
            failover.TCPCheck(LOOPBACK, service.port,
                                       failover.second(10)))

        # Add another with an integer time value
        server.add_component(
            'always-succeed2',
            failover.TCPCheck(LOOPBACK, service.port, 10))

        checker = failover.TCPCheck(
            UNROUTABLE, 80, failover.second(0.1))
        server.add_component('always-fail', checker)

        # Make sure checker got a name
        self.assertEqual(repr(checker), "always-fail")

        # Add a service-name check
        checker = failover.TCPCheck(
            UNROUTABLE, "http", failover.second(0.1))
        server.add_component('always-fail2', checker)

        # Try adding an un-callable object
        server.add_component('wrong', 4)

        # Run the HTTP server in a separate thread
        start_server(server)
        
        try:
            # always-succeed should always return ok
            con = HTTPConnection(LOOPBACK, server.port)
            con.request("GET", "/always-succeed")
            response = con.getresponse()
            self.assertEqual(response.status, OK)

            con.request("GET", "/always-succeed2")
            response = con.getresponse()
            self.assertEqual(response.status, OK)

            # always-fail should always return service unavailable
            con.request("GET", "/always-fail")
            response = con.getresponse()
            self.assertEqual(response.status, SERVICE_UNAVAILABLE)

            # HEAD requests should return the same.
            con.request("HEAD", "/always-fail")
            response = con.getresponse()
            self.assertEqual(response.status, SERVICE_UNAVAILABLE)

            # A non-existent service should return not found
            con.request("GET", "/unknown")
            response = con.getresponse()
            self.assertEqual(response.status, NOT_FOUND)

            # Uncallable service should return 500
            con.request("GET", "/wrong")
            response = con.getresponse()
            self.assertEqual(response.status, INTERNAL_SERVER_ERROR)
        finally:
            log.info("Exiting TCP server")
            service.exit_requested = True
            service.join()

            log.info("Exiting health check server")
            stop_server(server)
            
        return

    def test_reject_invalid_hostname(self):
        try:
            failover.TCPCheck(3.14159, 90, failover.second(1))
            self.fail("Expected TypeError")
        except TypeError:
            pass

    def test_reject_invalid_port(self):
        for port in [-2, -1, 0, 65536, 131072, "myxlflyx"]:
            try:
                failover.TCPCheck(LOOPBACK, port, failover.second(1))
                self.fail("Expected ValueError")
            except ValueError:
                pass

        try:
            failover.TCPCheck(LOOPBACK, None, failover.second(1))
            self.fail("Expected TypeError")
        except TypeError:
            pass

    def test_reject_invalid_duration(self):
        try:
            failover.TCPCheck(LOOPBACK, 80, failover.second(-1))
            self.fail("Expected ValueError")
        except ValueError:
            pass

        try:
            failover.TCPCheck(LOOPBACK, 80, -1)
            self.fail("Expected ValueError")
        except ValueError:
            pass

        try:
            failover.TCPCheck(LOOPBACK, 80, -1.5)
            self.fail("Expected ValueError")
        except ValueError:
            pass

        try:
            failover.TCPCheck(LOOPBACK, 80, failover.count(1))
            self.fail("Expected ValueError")
        except ValueError:
            pass

        try:
            failover.TCPCheck(LOOPBACK, 80, [1,2,3])
            self.fail("Expected TypeError")
        except TypeError:
            pass


if __name__ == "__main__":
    main()
