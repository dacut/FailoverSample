#!/usr/bin/env python
from __future__ import absolute_import, print_function
from base64 import b64decode, b64encode
import ctypes as c
from .handler import current_handler
from logging import getLogger

log = getLogger("failover.auth.apache")

class ApachePasswdFileCheck(object):
    def __init__(self, filename):
        super(ApachePasswdFileCheck, self).__init__()
        # Make sure libaprutil-1 exists on this system.
        for ext in (".dylib", ".sl", ".so"):
            try:
                log.info("Trying libaprutil-1" + ext)
                self.libaprutil = c.CDLL("libaprutil-1" + ext)
                break
            except OSError as e: # pragma: nocover
                log.error("Failed to load libaprutil-1" + ext, exc_info=1)
        else: # pragma: nocover
            raise RuntimeError("libaprutil-1 not found")

        self.libaprutil.apr_password_validate.argtypes = (
            c.c_char_p, c.c_char_p)
        self.libaprutil.apr_password_validate.restype = c.c_int
        self.filename = filename
        return

    def __call__(self):
        handler = current_handler()
        if handler is None:
            log.error("No current HTTP handler available!")
            raise RuntimeError("No current HTTP handler available!")

        client_auth = handler.headers.get("Authorization", None)
        if client_auth is None:
            log.info("No Authorization header sent")
            return False

        try:
            client_method, client_payload = client_auth.split(" ", 1)
        except ValueError:
            log.info("Invalid Authorization header %r", client_auth)
            return False

        if client_method != "Basic":
            log.info("Unsupported authentication method %r", client_method)
            return False

        try:
            client_decoded = b64decode(client_payload)
            client_username, client_password = client_decoded.split(":", 1)
        except ValueError as e:
            log.info("Unable to decode payload %r: %s", client_payload, e)
            return False

        try:
            fd = open(self.filename)
        except IOError as e:
            log.error("Unable to open %s: %s", self.filename, e)
            raise

        try:
            for lineno, line in enumerate(fd, 1):
                try:
                    username, pwhash = line.strip().split(":", 1)
                except ValueError:
                    log.error(
                        "In file %s, line %d: invalid syntax (missing ':')",
                        self.filename, line)
                    continue

                if username != client_username:
                    continue

                if (self.libaprutil.apr_password_validate(
                        client_password, pwhash) == 0):
                    log.info("Authorization succeeded for %s", username)
                    return True

                # Keep reading the file in case there are multiple
                # possibilities for this user (unlikely).
        finally:
            fd.close()
        
        return False
