#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''\
usage: venv-update [-h] [virtualenv_dir] [requirements [requirements ...]]

Update a (possibly non-existant) virtualenv directory using a requirements.txt listing
When this script completes, the virtualenv should have the same packages as if it were
removed, then rebuilt.

To set the index server, export a PIP_INDEX_URL variable.
    See also: https://pip.readthedocs.org/en/stable/user_guide/#environment-variables

positional arguments:
  virtualenv_dir  Destination virtualenv directory (default: virtualenv_run)
  requirements    Requirements files. (default: requirements.txt)

optional arguments:
  -h, --help      show this help message and exit

Version control at: https://github.com/yelp/pip-faster
'''
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

__version__ = '0.1.4.4'

# This script must not rely on anything other than
#   stdlib>=2.6 and virtualenv>1.11


def parseargs(args):
    if set(args) & set(('-h', '--help')):
        print(__doc__, end='')
        exit(0)

    args = list(args)
    virtualenv_dir = None
    requirements = []
    remaining = []

    for arg in args:
        if arg.startswith('-'):
            remaining.append(arg)
        elif virtualenv_dir is None:
            virtualenv_dir = arg
        else:
            requirements.append(arg)

    if not virtualenv_dir:
        virtualenv_dir = 'virtualenv_run'
    if not requirements:
        requirements = ['requirements.txt']

    return virtualenv_dir, tuple(requirements), tuple(remaining)


def timid_relpath(arg):
    from os.path import isabs, relpath
    if isabs(arg):
        result = relpath(arg)
        if len(result) < len(arg):
            return result

    return arg


def shellescape(args):
    from pipes import quote
    return ' '.join(quote(timid_relpath(arg)) for arg in args)


def colorize(cmd):
    from os import isatty

    if isatty(1):
        template = '\033[01;36m>\033[m \033[01;32m{0}\033[m'
    else:
        template = '> {0}'

    return template.format(shellescape(cmd))


def run(cmd):
    from subprocess import check_call
    check_call(('echo', colorize(cmd)))
    check_call(cmd)


def info(msg):
    # use a subprocess to ensure correct output interleaving.
    from subprocess import check_call
    check_call(('echo', msg))


def validate_venv(venv_path, venv_args):
    """Ensure we have a valid virtualenv."""
    import json
    from sys import executable, version
    from virtualenv import __version__ as virtualenv_version
    # we count any existing virtualenv invalidated if any of these relevant values changes
    validation = (
        version,  # includes e.g. pypy version
        virtualenv_version,
        venv_args,
        venv_path,
    )
    # normalize types, via json round-trip
    validation = json.loads(json.dumps(validation))

    from os.path import join, abspath
    venv_path = abspath(venv_path)  # this removes trailing slashes as well
    state_path = join(venv_path, '.venv-update.state')

    from os.path import isdir
    if isdir(venv_path):
        try:
            with open(state_path) as state:
                previous_state = json.load(state)
        except IOError:
            previous_state = {}

        if previous_state.get('validation') == validation:
            info('Keeping virtualenv from previous run.')
            return
        else:
            info('Removing invalidated virtualenv.')
            run(('rm', '-rf', venv_path))

            # run virtualenv using the same executable as last time
            # this avoids running virtualenv against its own container
            executable = previous_state.get('executable', executable)

    run((executable, '-m', 'virtualenv', venv_path) + venv_args)

    if isdir(venv_path):
        with open(state_path, 'w') as state:
            json.dump(
                dict(executable=executable, validation=validation),
                state,
            )


def wait_for_all_subprocesses():
    from os import wait
    try:
        while True:
            wait()
    except OSError as error:
        if error.errno == 10:  # no child processes
            return
        else:
            raise


def backintime(reference, filename):
    info(colorize(('touch', filename, '--reference', reference, '--date', '1 day ago')))
    from os.path import getmtime
    mtime = getmtime(reference)

    timestamp = mtime - 24 * 60 * 60

    from os import utime
    utime(filename, (timestamp, timestamp))


def mark_venv_invalid(venv_path, reqs):
    # LBYL, to attempt to avoid any exception during exception handling
    from os.path import isdir, exists
    if isdir(venv_path) and exists(reqs[0]):
        info('')
        info("Something went wrong! Sending '%s' back in time, so make knows it's invalid." % timid_relpath(venv_path))
        info('Waiting for all subprocesses to finish...')
        wait_for_all_subprocesses()
        info('DONE')
        backintime(reqs[0], venv_path)
        info('')


def dotpy(filename):
    if filename.endswith(('.pyc', '.pyo', '.pyd')):
        return filename[:-1]
    else:
        return filename


def venv_executable(venv_path, executable):
    from os.path import join
    return join(venv_path, 'bin', executable)


def venv_python(venv_path):
    return venv_executable(venv_path, 'python')


def venv_update(venv_path, reqs, venv_args):
    """we have an arbitrary python interpreter active, (possibly) outside the virtualenv we want.

    make a fresh venv at the right spot, make sure it has pip-faster, and use it
    """
    from os.path import abspath
    venv_path = abspath(venv_path)
    validate_venv(venv_path, venv_args)
    from os.path import exists
    python = venv_python(venv_path)
    if not exists(python):
        return 'virtualenv executable not found: %s' % python

    # ensure that a compatible version of pip is installed
    run((python, '-m', 'pip.__main__', '--version'))

    from os import environ
    pipdir = environ['HOME'] + '/.pip'
    # We could combine these caches to one directory, but pip would search everything twice, going slower.
    pip_wheels = pipdir + '/wheelhouse'

    # TODO: short-circuit when pip-faster is already there.
    run((
        python, '-m', 'pip.__main__', 'install',
        '--find-links=file://' + pip_wheels,
        'pip-faster==' + __version__
    ))

    run((python, '-m', 'pip_faster', 'install', '--prune') + sum(
        [('-r', req) for req in reqs],
        (),
    ))


def main():
    from sys import argv, path
    del path[:1]  # we don't (want to) import anything from pwd or the script's directory
    venv_path, reqs, venv_args = parseargs(argv[1:])

    from subprocess import CalledProcessError
    try:
        return venv_update(venv_path, reqs, venv_args)
    except SystemExit as error:
        exit_code = error.code
    except CalledProcessError as error:
        exit_code = error.returncode
    except KeyboardInterrupt:
        exit_code = 1
    except Exception as error:
        mark_venv_invalid(venv_path, reqs)
        raise

    if exit_code != 0:
        mark_venv_invalid(venv_path, reqs)

    return exit_code


if __name__ == '__main__':
    exit(main())
