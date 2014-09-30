# pylint:disable=superfluous-parens

import distutils
import os
import os.path
import subprocess
import sys

orig_args = None


def extend_parser(dummy_parser):
    global orig_args  # pylint:disable=global-statement
    orig_args = list(sys.argv)
    sys.argv[:] = os.path.join(os.environ['HOME'], '.venv-update')


def after_install(dummy_options, home_dir):
    subprocess.check_call([
        os.path.join(home_dir, 'bin', 'pip'),
        'install', 'pre-commit',
    ])

    bin_dir = os.path.join(os.environ['HOME'], 'bin')
    script_src = os.path.join(home_dir, 'bin', 'pre-commit')
    script_dest = os.path.join(bin_dir, 'pre-commit')
    print('*' * 79)
    print('Installing pre-commit to {0}'.format(script_dest))
    print('*' * 79)

    if not os.path.exists(bin_dir):
        os.mkdir(bin_dir)

    # os.symlink is not idempotent
    if os.path.exists(script_dest):
        os.remove(script_dest)

    os.symlink(script_src, script_dest)

    if not distutils.spawn.find_executable('pre-commit'):
        print('It looks like {0} is not on your path'.format(bin_dir))
        print('You may want to add it.')
        print('Often this does the trick: source ~/.profile')
