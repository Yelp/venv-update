"""
Show a command's output in realtime and capture its outputs as strings,
without deadlocking or temporary files.

This should maybe be a package in its own right, someday.
"""
from __future__ import print_function

import os
from subprocess import Popen, CalledProcessError


# posix standard file descriptors
STDIN, STDOUT, STDERR = range(3)
PY3 = (str is not bytes)

if hasattr(os, 'set_inheritable'):
    # os.set_inheritable only exists in py3  pylint:disable=no-member
    set_inheritable = os.set_inheritable
else:
    def set_inheritable(*_):
        pass


def fdclosed(fd):
    """close a file descriptor, idempotently"""
    try:
        os.close(fd)
    except OSError as err:
        if err.errno == 9:  # bad file descriptor
            pass  # it's already closed: ok
        else:
            raise


class Pipe(object):
    """a convenience object, wrapping os.pipe()"""
    def __init__(self):
        self.read, self.write = os.pipe()
        # emulate old, inheritable os.pipe in py34
        set_inheritable(self.read, True)
        set_inheritable(self.write, True)

    def closed(self):
        """close both ends of the pipe. idempotent."""
        fdclosed(self.read)
        fdclosed(self.write)

    def readonly(self):
        """close the write end of the pipe. idempotent."""
        fdclosed(self.write)


def pty_normalize_newlines(fd):
    r"""
    Twiddle the tty flags such that \n won't get munged to \r\n.
    Details:
        https://docs.python.org/2/library/termios.html
        http://ftp.gnu.org/old-gnu/Manuals/glibc-2.2.3/html_chapter/libc_17.html#SEC362
    """
    import termios as T
    attrs = T.tcgetattr(fd)
    attrs[1] &= ~(T.ONLCR | T.OPOST)
    T.tcsetattr(fd, T.TCSANOW, attrs)


class Pty(Pipe):
    """Represent a pty as a pipe"""
    def __init__(self):  # pylint:disable=super-init-not-called
        self.read, self.write = os.openpty()
        pty_normalize_newlines(self.read)


def read_block(fd, block=4 * 1024):
    """Read up to 4k bytes from fd.
    Returns empty-string upon end of file.
    """
    from os import read
    try:
        return read(fd, block)
    except OSError as error:
        if error.errno == 5:
            # pty end-of-file, sometimes:
            #   http://bugs.python.org/issue21090#msg231093
            return b''
        else:
            raise


def read_all(fd):
    """My own read loop, bc the one in python3.4 is derpy atm:
    http://bugs.python.org/issue21090#msg231093
    """
    from os import close

    result = []
    lastread = None
    while lastread != b'':
        lastread = read_block(fd)
        result.append(lastread)
    close(fd)
    return b''.join(result)


class Tee(object):
    """send output from read_fd to each of write_fds
    call .join() to get a complete copy of output
    """
    def __init__(self, read_fd, *write_fds):
        self.read = read_fd
        self.write = write_fds
        self._result = []

        from threading import Thread
        self.thread = Thread(target=self.tee)
        self.thread.start()

    def tee(self):
        line = read_block(self.read)
        while line != b'':
            self._result.append(line)
            for w in self.write:
                os.write(w, line)
            line = read_block(self.read)
        os.close(self.read)

    def join(self):
        self.thread.join()
        return b''.join(self._result)


def capture_subprocess(cmd, encoding='UTF-8', **popen_kwargs):
    """Run a command, showing its usual outputs in real time,
    and return its stdout, stderr output as strings.

    No temporary files are used.
    """
    stdout = Pty()  # libc uses full buffering for stdout if it doesn't see a tty
    stderr = Pipe()

    # deadlocks occur if we have any write-end of a pipe open more than once
    # best practice: close any used write pipes just after spawn
    outputter = Popen(
        cmd,
        stdout=stdout.write,
        stderr=stderr.write,
        **popen_kwargs
    )
    stdout.readonly()  # deadlock otherwise
    stderr.readonly()  # deadlock otherwise

    # start one tee each on the original stdout and stderr
    # writing each to three places:
    #    1. the original destination
    #    2. a pipe just for that one stream
    stdout_tee = Tee(stdout.read, STDOUT)
    stderr_tee = Tee(stderr.read, STDERR)

    # clean up left-over processes and pipes:
    exit_code = outputter.wait()
    result = (stdout_tee.join(), stderr_tee.join())

    if encoding is not None:
        result = tuple(
            bytestring.decode(encoding)
            for bytestring in result
        )

    if exit_code == 0:
        return result
    else:
        error = CalledProcessError(exit_code, cmd)
        error.result = result
        raise error
