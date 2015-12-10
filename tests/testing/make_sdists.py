from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from sys import executable as python


def info(*msg):
    from sys import stdout
    stdout.write(' '.join(str(x) for x in msg))
    stdout.write('\n')
    stdout.flush()


def random_string():
    """return a short suffix that shouldn't collide with any subsequent calls"""
    import os
    import string
    import random

    return '{}.{}'.format(
        os.getpid(),
        ''.join(random.choice(string.ascii_lowercase) for x in range(8)),
    )


def sdist(setuppy, dst):
    import subprocess
    info('sdist', setuppy.dirname)
    subprocess.check_call(
        (python, 'setup.py', 'sdist', '--dist-dir', str(dst)),
        cwd=setuppy.dirname,
    )


def build_one(src, dst):
    setuppy = src.join('setup.py')
    if setuppy.exists():
        sdist(setuppy, dst)

        if src.join('wheelme').exists():
            wheel(src, dst)

        return True


def build_all(sources, dst):
    for source in sources:
        if build_one(source, dst):
            continue
        for source in source.listdir():
            if not source.check(dir=True):
                continue

            build_one(source, dst)


def flock(path):
    import os
    fd = os.open(path, os.O_CREAT)

    import fcntl
    fcntl.flock(fd, fcntl.LOCK_EX)  # exclusive

    return fd


class public_pypi_enabled(object):
    orig = None

    def __enter__(self):
        from os import environ
        self.orig = environ.pop('PIP_INDEX_URL', None)

    def __exit__(self, value, type_, traceback):
        from os import environ
        if self.orig is not None:
            environ['PIP_INDEX_URL'] = self.orig


def wheel(src, dst):
    import subprocess
    info('wheel', src)

    with public_pypi_enabled():
        subprocess.check_call(
            (python, '-m', 'pip.__main__', 'wheel', '--wheel-dir', str(dst), str(src)),
        )


def download_sdist(source, destination):
    import subprocess
    info('download sdist', source)
    with public_pypi_enabled():
        subprocess.check_call(
            (python, '-m', 'pip.__main__', 'install', '-d', str(destination), str(source), '--no-use-wheel', '--no-deps'),
        )


def make_sdists(sources, destination):
    destination.dirpath().ensure(dir=True)

    lock = destination.new(ext='lock')
    flock(lock.strpath)

    staging = destination.new(ext=random_string() + '.tmp')
    staging.ensure(dir=True)

    build_all(sources, staging)
    wheel('argparse', staging)
    wheel('coverage-enable-subprocess', staging)
    download_sdist('coverage', staging)
    download_sdist('coverage-enable-subprocess', staging)

    if destination.islink():
        old = destination.readlink()
    else:
        old = None

    link = staging.new(ext='ln')
    link.mksymlinkto(staging, absolute=False)
    link.rename(destination)

    if old is not None:
        destination.dirpath(old).remove()


def main():
    from sys import argv
    sources, destination = argv[1:-1], argv[-1]

    from py._path.local import LocalPath
    sources = tuple([
        LocalPath(src) for src in sources
    ])
    destination = LocalPath(destination)

    return make_sdists(sources, destination)


if __name__ == '__main__':
    exit(main())
