#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
    Update a (possibly non-existant) virtualenv directory using a requirements.txt listing
    When this script completes, the virtualenv should have the same packages as if it were
    removed, then rebuilt.
'''
from __future__ import print_function

import argparse
from contextlib import contextmanager
from os import environ
from os.path import exists, isdir
from plumbum import local

from venv_update._compat import exec_file


def parseargs(args):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('virtualenv_dir', help='Destination virtualenv directory')
    parser.add_argument('requirements', nargs='+', help='Requirements files.')
    parsed_args = parser.parse_args(args)

    return parsed_args.virtualenv_dir, parsed_args.requirements


def colorize(pbcmd, *args):
    pbcmd = pbcmd[args]
    local['echo']['\033[01;36m>\033[m \033[01;33m{0}\033[m'.format(
        ' '.join(pbcmd.formulate(level=1))
    )].run(stdin=None, stdout=None, stderr=None)
    local['time'][pbcmd].run(stdin=None, stdout=None, stderr=None)


@contextmanager
def clean_venv(venv_path):
    """Make a clean virtualenv, and activate it."""
    if exists(venv_path):
        # virtualenv --clear has two problems:
        #   it doesn't properly clear out the venv/bin, causing wacky errors
        #   it writes over (rather than replaces) the python binary, so there's an error if it's in use.
        colorize(local['rm'], '-rf', venv_path)

    virtualenv = local['virtualenv'][venv_path]
    colorize(virtualenv, '--system-site-packages')

    # This is the documented way to activate the venv in a python process.
    activate_this_file = venv_path + "/bin/activate_this.py"
    exec_file(activate_this_file, dict(__file__=activate_this_file))
    local.env.update(environ)

    yield

    # Postprocess: Make our venv relocatable, since we do plan to relocate it, sometimes.
    colorize(virtualenv, '--relocatable')


def do_install(reqs):
    requirements_as_options = [
        '--requirement={0}'.format(requirement) for requirement in reqs
    ]

    # See also: http://pip.readthedocs.org/en/latest/user_guide.html#environment-variables
    pip_index_url = 'https://pypi.yelpcorp.com/simple/'

    # We put the cache in the directory that pip already uses.
    # This has better security characteristics than a machine-wide cache, and is a
    #   pattern people can use for open-source projects
    pip_download_cache = environ['HOME'] + '/.pip/cache'

    local.env.update(
        PIP_INDEX_URL=pip_index_url,
        PIP_DOWNLOAD_CACHE=pip_download_cache,
    )

    # We need python -m here so that the system-level pip1.4 knows we're talking about the venv.
    pip = local['python']['-m', 'pip.runner']

    cache_opts = (
        '--download-cache=' + pip_download_cache,
        '--find-links=file://' + pip_download_cache,
        '--index-url=' + pip_index_url,
    )

    # --use-wheel is somewhat redundant here, but it means we get an error if we have a bad version of pip/setuptools.
    install = pip['install', '--ignore-installed', '--use-wheel'][cache_opts]
    wheel = pip['wheel'][cache_opts]

    # Bootstrap the install system; setuptools and pip are alreayd installed, just need wheel
    colorize(install, 'wheel')

    # Caching: Make sure everything we want is downloaded, cached, and has a wheel.
    colorize(
        wheel,
        '--wheel-dir=' + pip_download_cache,
        requirements_as_options,
        'wheel',
    )

    # Install: Use our well-populated cache (only) to do the installations.
    # The --ignore-installed gives more-repeatable behavior in the face of --system-site-packages,
    #   and brings us closer to a --no-site-packages future
    colorize(install, '--no-index', requirements_as_options)

    return 0


def mark_venv_invalid(venv_path, reqs):
    if isdir(venv_path):
        print()
        print("Something went wrong! Sending %r back in time, so make knows it's invalid." % venv_path)
        colorize(local['touch'], venv_path, '--reference', reqs[0], '--date', '1 day ago')
        print()


def main():
    import sys
    from plumbum import ProcessExecutionError
    venv_path, reqs = parseargs(sys.argv[1:])

    try:
        with clean_venv(venv_path):
            exit_code = do_install(reqs)
    except SystemExit as error:
        exit_code = error.code
    except ProcessExecutionError as error:
        exit_code = error.retcode
    except KeyboardInterrupt:
        exit_code = 1
    except Exception:
        mark_venv_invalid(venv_path, reqs)
        raise

    if exit_code != 0:
        mark_venv_invalid(venv_path, reqs)

    return exit_code


# Test scenarios: (not implemented yet :( )
#   * entirely clean -- <venv_path> does not exist
#   * noop -- Requirements haven't changed since last run
#   * each of these should behave similarly whether caused by the user or the requirements file:
#       * upgrade
#       * downgrade
#       * add
#       * delete

manual_tests = dict(
    smoketest='''
rm -rf virtualenv_run ~/.pip
time make virtualenv_run    # should run in ~100s
touch requirements.txt
time make virtualenv_run    # should be speedy: ~12.5s
    ''',
    text_file_busy=''',
time make virtualenv_run
source virtualenv_run/bin/activate
touch requirements.txt
time make virtualenv_run  # should succeed
    ''',
    output_interleaving='''
touch requirements.txt
time make virtualenv_run | tee virtrualenv_run.log  # should show the commands in proper position
    ''',
    scripts_left_behind=''',
time make virtualenv_run
source virtualenv_run/bin/activate
pip install --upgrade virtualenv
touch requirements.txt
time make virtualenv_run
which virtualenv  # should show /usr/bin/virtualenv
virtualenv --version  # should succeed
    ''',
    failure_rerun='''
make virtualenv_run
echo 'foo' >> requirements.txt
make virtualenv_run  # Should fail
make virtualenv_run  # Should try again and fail again
git checkout -- requirements.txt
make virtualenv_run  # Should succeed
    ''',
    failure_with_requirements_dev='''
make virtualenv_run
echo 'foo' >> requirements-dev.txt
make virtualenv_run  # Should fail
make virtualenv_run  # Should try again and fail again
git checkout -- requirements-dev.txt
make virtualenv_run  # Should succeed
    ''',
    freshen_venv_update='''
bootstrap re-installs venv-update when there's been a change to bootstrap script,
or to the venv-update spec
    ''',
    no_freshen_venv_update='''
bootstrap doesn't re-install venv-update when there's been no change to bootstrap script
nor the venv-update spec
    ''',
    freshen_venv='''
already in the venv created by venv-update
run venv-update bootstrapper to freshen it
    ''',
)


if __name__ == '__main__':
    exit(main())
