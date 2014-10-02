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


def after_install(dummy_options, home_dir):
    subprocess.check_call([
        os.path.join(home_dir, 'bin', 'pip'),
        'install', 'venv-update',
    ])

    script_src = os.path.join(home_dir, 'bin', 'venv-update')
    subprocess.check_call([script_src] + orig_args)
