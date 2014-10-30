#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
    Update a (possibly non-existant) virtualenv directory using a requirements.txt listing
    When this script completes, the virtualenv should have the same packages as if it were
    removed, then rebuilt.

    To set the index server, export a PIP_INDEX_SERVER variable.
        See also: http://pip.readthedocs.org/en/latest/user_guide.html#environment-variables
'''
from __future__ import print_function
from __future__ import unicode_literals
from contextlib import contextmanager
from os import environ
from os.path import exists, isdir


# The versions of these bootstrap packages are semi-pinned, to give us bugfixes but mitigate incompatiblity.
WHEEL = 'wheel>=0.22.0,<1.0'

HELP_OUTPUT = '''\
usage: venv-update [-h] [virtualenv_dir] [requirements [requirements ...]]

Update a (possibly non-existant) virtualenv directory using a requirements.txt
listing When this script completes, the virtualenv should have the same
packages as if it were removed, then rebuilt. To set the index server, export
a PIP_INDEX_SERVER variable. See also:
http://pip.readthedocs.org/en/latest/user_guide.html#environment-variables

positional arguments:
  virtualenv_dir  Destination virtualenv directory (default: virtualenv_run)
  requirements    Requirements files. (default: requirements.txt)

optional arguments:
  -h, --help      show this help message and exit
'''


def parseargs(args):
    if set(args) & set(['-h', '--help']):
        print(HELP_OUTPUT, end='')
        exit(0)

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


def colorize(cmd, *args):
    from os import isatty

    cmd = cmd + args
    if isatty(1):
        template = '\033[01;36m>\033[m \033[01;33m{0}\033[m'
    else:
        template = '> {0}'

    from subprocess import check_call
    from pipes import quote
    check_call(('echo', template.format(
        ' '.join(quote(arg) for arg in cmd)
    )))
    check_call(cmd)


def exec_file(fname, lnames=None, gnames=None):
    """a python3 replacement for execfile"""
    with open(fname) as f:
        code = compile(f.read(), fname, 'exec')
        exec(code, lnames, gnames)  # pylint:disable=exec-used


@contextmanager
def clean_venv(venv_path, venv_args):
    """Make a clean virtualenv, and activate it."""
    if exists(venv_path):
        # virtualenv --clear has two problems:
        #   it doesn't properly clear out the venv/bin, causing wacky errors
        #   it writes over (rather than replaces) the python binary, so there's an error if it's in use.
        colorize(('rm', '-rf', venv_path))

    virtualenv = ('virtualenv', venv_path)
    colorize(virtualenv + venv_args)

    # This is the documented way to activate the venv in a python process.
    activate_this_file = venv_path + "/bin/activate_this.py"
    exec_file(activate_this_file, dict(__file__=activate_this_file))

    yield

    # Postprocess: Make our venv relocatable, since we do plan to relocate it, sometimes.
    colorize(virtualenv, '--relocatable')


def do_install(reqs):
    requirements_as_options = tuple(
        '--requirement={0}'.format(requirement) for requirement in reqs
    )

    # We put the cache in the directory that pip already uses.
    # This has better security characteristics than a machine-wide cache, and is a
    #   pattern people can use for open-source projects
    pip_download_cache = environ['HOME'] + '/.pip/cache'

    environ.update(
        PIP_DOWNLOAD_CACHE=pip_download_cache,
    )

    # We need python -m here so that the system-level pip1.4 knows we're talking about the venv.
    pip = ('python', '-m', 'pip.runner')

    cache_opts = (
        '--download-cache=' + pip_download_cache,
        '--find-links=file://' + pip_download_cache,
    )

    install = pip + ('install', '--ignore-installed') + cache_opts
    # --use-wheel is somewhat redundant here, but it means we get an error if we have a bad version of pip/setuptools.
    install = install + ('--use-wheel',)  # yay!
    wheel = pip + ('wheel',) + cache_opts

    # Bootstrap: Get pip the tools it needs.
    colorize(install, WHEEL)

    # Caching: Make sure everything we want is downloaded, cached, and has a wheel.
    colorize(
        wheel,
        '--wheel-dir=' + pip_download_cache,
        WHEEL,
        *requirements_as_options
    )

    # Install: Use our well-populated cache (only) to do the installations.
    # The --ignore-installed gives more-repeatable behavior in the face of --system-site-packages,
    #   and brings us closer to a --no-site-packages future
    colorize(install, '--no-index', *requirements_as_options)

    return 0


def mark_venv_invalid(venv_path, reqs):
    if isdir(venv_path):
        print()
        print("Something went wrong! Sending '%s' back in time, so make knows it's invalid." % venv_path)
        colorize(('touch', venv_path, '--reference', reqs[0], '--date', '1 day ago'))
        print()


def main():
    import sys
    venv_path, reqs, venv_args = parseargs(sys.argv[1:])

    from subprocess import CalledProcessError
    try:
        with clean_venv(venv_path, venv_args):
            exit_code = do_install(reqs)
    except SystemExit as error:
        exit_code = error.code
    except CalledProcessError as error:
        exit_code = error.returncode
    except KeyboardInterrupt:
        exit_code = 1
    except Exception:
        mark_venv_invalid(venv_path, reqs)
        raise

    if exit_code != 0:
        mark_venv_invalid(venv_path, reqs)

    return exit_code


if __name__ == '__main__':
    exit(main())
