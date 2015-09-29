from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import errno
import socket
from socket import getfqdn
from socket import SO_REUSEADDR
from socket import socket as Socket
from socket import SOL_SOCKET

from testing.ephemeral_port_reserve import LOCALHOST
from testing.ephemeral_port_reserve import reserve


def bind_naive(ip, port):
    sock = Socket()
    try:
        sock.bind((ip, port))
    except socket.error as error:
        return error


def bind_reuse(ip, port):
    sock = Socket()
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind((ip, port))
    return sock


def assert_ip(ip):
    port = reserve(ip)

    # show that we can't bind to it without SO_REUSEADDR
    error = bind_naive(ip, port)
    assert error and error.errno == errno.EADDRINUSE, error

    # show that we *can* bind to it without SO_REUSEADDR, after release
    sock = bind_reuse(ip, port)
    sname = sock.getsockname()
    assert sname == (ip, port), (sname, port)


def test_localhost():
    assert_ip(LOCALHOST)


def test_fqdn():
    fqip = socket.gethostbyname(getfqdn())
    assert_ip(fqip)
