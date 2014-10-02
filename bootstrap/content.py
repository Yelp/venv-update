# pylint:disable=superfluous-parens

import os
import os.path
import subprocess
import sys

orig_args = None


def extend_parser(dummy_parser):
    global orig_args  # pylint:disable=global-statement
    orig_args = sys.argv[1:]
    sys.argv[1:] = [os.path.join(os.environ['HOME'], '.venv-update')]


def activate(venv):
    activate_this = os.path.join(venv, 'bin', 'activate_this.py')
    code = open(activate_this).read()
    code = compile(code, activate_this, 'exec')
    exec(code, {'__file__': activate_this})  # pylint:disable=exec-used


def after_install(dummy_options, home_dir):
    subprocess.check_call([
        os.path.join(home_dir, 'bin', 'pip'),
        'install', 'venv-update',
    ])

    activate(home_dir)

    script_src = os.path.join(home_dir, 'bin', 'venv-update')
    os.execv(script_src, [script_src] + orig_args)
