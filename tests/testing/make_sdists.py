from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals


def random_string():
    """return a short suffix that shouldn't collide with any subsequent calls"""
    import os
    import base64

    return '.'.join((
        str(os.getpid()),
        base64.urlsafe_b64encode(os.urandom(3)),
    ))


def sdist(setuppy, dst):
    import subprocess
    import sys
    print('sdist', setuppy.dirname)
    subprocess.check_call(
        (sys.executable, 'setup.py', 'sdist', '--dist-dir', str(dst)),
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


def wheel(src, dst):
    import subprocess
    import sys
    import os
    print('wheel', src)

    # explicitly enable default PIP_INDEX_URL
    env = os.environ.copy()
    env.pop('PIP_INDEX_URL', None)

    subprocess.check_call(
        (sys.executable, '-m', 'pip.__main__', 'wheel', '--wheel-dir', str(dst), str(src)),
        env=env,
    )


def make_sdists(sources, destination):
    destination.dirpath().ensure(dir=True)

    lock = destination.new(ext='lock')
    flock(lock.strpath)

    staging = destination.new(ext=random_string() + '.tmp')
    staging.ensure(dir=True)

    build_all(sources, staging)
    wheel('argparse', staging)
    wheel('coverage', staging)

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
