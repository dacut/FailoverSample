from __future__ import absolute_import, print_function
import failover
import logging
from select import select
from socket import (AF_INET, INADDR_ANY, SOCK_STREAM, socket, SOL_SOCKET,
                    SO_REUSEADDR)
from sys import stderr
from threading import Thread, Condition
from time import sleep
from unittest import TestCase, main

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
                try:
                    self.lock.wait(0.1)
                except RuntimeError:
                    pass

                if self.socket:
                    log.debug("Waiting for connection")
                    result = select([self.socket], [], [], self.timeout)
                    if result:
                        log.debug("Healthy -- received connection")
                        conn, client = self.socket.accept()
                        self.discard(conn)
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
        checker = failover.check_tcp_service(
            LOOPBACK, service.port, failover.second(10))
        
        self.assertTrue(checker())
        service.close()
        self.assertFalse(checker())
        service.listen()
        self.assertTrue(checker())
        self.assertTrue(checker())
        
        service.exit_requested = True
        service.join()
        return

    def test_unroutable(self):
        checker = failover.check_tcp_service(
            UNROUTABLE, 80, failover.second(0.1))

        self.assertFalse(checker())
        return

if __name__ == "__main__":
    main()
