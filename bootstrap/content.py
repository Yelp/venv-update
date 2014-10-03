# pylint:disable=superfluous-parens

import os
from os.path import exists, getmtime, join
import subprocess
import sys

VENV_REQ = 'requirements.d/venv-update.txt'
VENV_HOME = join(os.environ['HOME'], '.venv-update')
VENV_UPDATE = join(VENV_HOME, 'bin', 'venv-update')

orig_args = None


def extend_parser(dummy_parser):
    """This callback is called before anything happens.
    We use it to store the original arguments and insert our own.
    """
    global orig_args  # pylint:disable=global-statement
    orig_args = sys.argv[1:]

    if exists(VENV_UPDATE) and getmtime(VENV_UPDATE) > getmtime(__file__):
        # TODO: use an md5sum rather than mtime
        # TODO: keep project's VENV_HOME's separate
        os.execv(VENV_UPDATE, [VENV_UPDATE] + orig_args)

    if hasattr(sys, 'real_prefix'):
        exit('You seem to be running from inside a virtualenv. Please deactivate and try again.')

    sys.argv[1:] = [VENV_HOME]


def adjust_options(dummy_options, dummy_args):
    """This callback is called just after parsing.
    We use it to ensure that the VENV_HOME doesn't exist before we install to it.
    """
    from subprocess import check_call
    check_call(['rm', '-rf', VENV_HOME])


def activate(venv):
    """Activate the virtualenv, in the current python process."""
    activate_this = join(venv, 'bin', 'activate_this.py')
    code = open(activate_this).read()
    code = compile(code, activate_this, 'exec')
    exec(code, {'__file__': activate_this})  # pylint:disable=exec-used


def after_install(dummy_options, dummy_home_dir):
    """This callback is called just after installing the virtualenv.
    We use it to install venv-update, and run it with the original arguments.
    """
    if exists(VENV_REQ):
        spec = ('-r', VENV_REQ)
    else:
        spec = ('venv-update',)

    subprocess.check_call(
        ('time', join(VENV_HOME, 'bin', 'pip'), 'install') + spec
    )

    activate(VENV_HOME)

    os.execv(VENV_UPDATE, [VENV_UPDATE] + orig_args)
