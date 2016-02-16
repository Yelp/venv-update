#!/usr/bin/python
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from socket import SO_REUSEADDR
from socket import socket
from socket import SOL_SOCKET

LOCALHOST = '127.0.0.1'


def reserve(ip=LOCALHOST):
    """Bind to an ephemeral port, force it into the TIME_WAIT state, and unbind it.

    This means that further ephemeral port alloctions won't pick this "reserved" port,
    but subprocesses can still bind to it explicitly, given that they use SO_REUSEADDR.
    By default on linux you have a grace period of 60 seconds to reuse this port.
    To check your own particular value:
    $ cat /proc/sys/net/ipv4/tcp_fin_timeout
    60

    By default, the port will be reserved for localhost (aka 127.0.0.1).
    To reserve a port for a different ip, provide the ip as the first argument.
    Note that IP 0.0.0.0 is interpreted as localhost.
    """
    server = socket()
    server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server.bind((ip, 0))
    server.listen(0)

    sockname = server.getsockname()

    # these three are necessary just to get the port into a TIME_WAIT state
    client = socket()
    client.connect(sockname)
    conn, _ = server.accept()

    server.close()
    conn.close()
    client.close()

    return sockname[1]


def main():
    from sys import argv
    port = reserve(*argv[1:])
    print(port)


if __name__ == '__main__':
    exit(main())
