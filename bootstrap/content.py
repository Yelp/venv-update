# pylint:disable=superfluous-parens

import os
from os.path import exists, getmtime, join
import sys

VENV_REQ = 'requirements.d/venv-update.txt'
VENV_HOME = join(os.environ['HOME'], '.venv-update')
VENV_UPDATE = join(VENV_HOME, 'bin', 'venv-update')

orig_args = None


def extend_parser(dummy_parser):
    """This runs before anything happens.
    We use it to store the original arguments and insert our own.
    """
    global orig_args  # pylint:disable=global-statement
    orig_args = tuple(sys.argv[1:])

    if exists(VENV_UPDATE) and getmtime(VENV_UPDATE) > getmtime(__file__):
        # TODO: use an md5sum rather than mtime
        # TODO: keep project's VENV_HOME's separate
        return after_install()

    if hasattr(sys, 'real_prefix'):
        exit('You seem to be running from inside a virtualenv. Please deactivate and try again.')

    sys.argv[1:] = [VENV_HOME]


def colorize(cmd):
    from subprocess import check_call
    from pipes import quote
    print '\033[01;36m>\033[m \033[01;33m{0}\033[m'.format(
        ' '.join(quote(arg) for arg in cmd)
    )
    check_call(cmd)


def adjust_options(dummy_options, dummy_args):
    """This runs just after option parsing.
    We use it to ensure that the VENV_HOME doesn't exist before we install to it.
    """
    colorize(('rm', '-rf', VENV_HOME))


def activate(venv):
    """Activate the virtualenv, in the current python process."""
    activate_this = join(venv, 'bin', 'activate_this.py')
    code = open(activate_this).read()
    code = compile(code, activate_this, 'exec')
    exec(code, {'__file__': activate_this})  # pylint:disable=exec-used


def after_install(dummy_options=None, dummy_home_dir=None):
    """This runs just after installing the virtualenv.
    We use it to install venv-update, and run it with the original arguments.
    """
    if exists(VENV_REQ):
        spec = ('-r', VENV_REQ)
    else:
        spec = ('venv-update',)

    activate(VENV_HOME)
    colorize(('time', 'pip', 'install', '--upgrade') + spec)
    os.execv(VENV_UPDATE, (VENV_UPDATE,) + orig_args)


acceptance_tests = dict(
    upgrade='''
change requirements.d/venv-update
use venv-update, shouldn't use old code
    ''',
)
