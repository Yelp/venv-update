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
    set_inheritable = lambda *args: None


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


class Pty(Pipe):
    """Represent a pty as a pipe"""
    def __init__(self):  # pylint:disable=super-init-not-called
        self.read, self.write = os.openpty()


def tee(read_fd, write_fd, *other_fds):
    """send output from read_fd to write_fd,
    but also copy it to each of other_fds
    """
    ischild = not os.fork()
    if ischild:
        os.dup2(read_fd, STDIN)
        os.dup2(write_fd, STDOUT)
        os.execvp(
            'tee',
            ('tee', ) + tuple(
                '/dev/fd/%i' % fd
                for fd in other_fds
            )
        )  # never returns
    os.close(read_fd)


def _communicate_with_select(read_set):
    """stolen from stdlib subprocess.Popen._communicate_with_select

    changes:
        arbitrary-length list of fds as input
        deleted stdin/input support
    """
    import select
    import errno

    orig_read_set = read_set
    read_set = list(read_set)
    result = {}
    for fd in read_set:
        result[fd] = []

    while read_set:
        try:
            readable, _, _ = select.select(read_set, [], [])
        except select.error as error:
            if error.args[0] == errno.EINTR:
                continue
            raise

        for fd in readable:
            data = os.read(fd, 1024)
            if data == b'':
                os.close(fd)
                read_set.remove(fd)
            result[fd].append(data)

    return tuple(
        b''.join(result[fd])
        for fd in orig_read_set
    )


def capture_subprocess(cmd, **popen_kwargs):
    """Run a command, showing its usual outputs in real time,
    and return its stdout, stderr, as well as combined output as strings.

    No temporary files are used.
    """
    stdout_orig = Pty()  # libc uses full buffering for stdout if it doesn't see a tty
    stderr_orig = Pipe()

    # deadlocks occur if we have any write-end of a pipe open more than once
    # best practice: close any used write pipes just after spawn
    outputter = Popen(
        cmd,
        stdout=stdout_orig.write,
        stderr=stderr_orig.write,
        **popen_kwargs
    )
    stdout_orig.readonly()  # deadlock otherwise
    stderr_orig.readonly()  # deadlock otherwise

    # start one tee each on the original stdout and stderr
    # writing each to three places:
    #    1. the original destination
    #    2. a pipe just for that one stream
    #    3. a pipe that shows the combined output
    stdout_teed = Pipe()
    stderr_teed = Pipe()
    combined = Pipe()

    tee(stdout_orig.read, STDOUT, stdout_teed.write, combined.write)
    tee(stderr_orig.read, STDERR, stderr_teed.write, combined.write)
    stdout_teed.readonly()  # deadlock otherwise
    stderr_teed.readonly()  # deadlock otherwise
    combined.readonly()  # deadlock otherwise

    # communicate closes fds when it's done with them
    result = _communicate_with_select((stdout_teed.read, stderr_teed.read, combined.read))

    # clean up left-over processes and pipes:
    exit_code = outputter.wait()
    stdout_teed.closed()
    stderr_teed.closed()
    combined.closed()

    # normalize newlines coming from the pty
    out, err, combined = result
    out = out.replace('\r\n', '\n')
    combined = combined.replace('\r\n', '\n')
    result = (out, err, combined)

    if exit_code == 0:
        return result
    else:
        error = CalledProcessError(exit_code, cmd)
        error.result = result
        raise error
