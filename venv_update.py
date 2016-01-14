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
  virtualenv_dir  Destination virtualenv directory (default: venv)
  requirements    Requirements files. (default: requirements.txt)

optional arguments:
  -h, --help      show this help message and exit

Version control at: https://github.com/yelp/pip-faster
'''
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from os.path import exists
from os.path import join

DEFAULT_VIRTUALENV_PATH = 'venv'
VENV_UPDATE_REQS_OVERRIDE = 'requirements.d/venv-update.txt'
__version__ = '1.0rc5'

# This script must not rely on anything other than
#   stdlib>=2.6 and virtualenv>1.11


def parseargs(args):
    """extremely rudimentary arg parsing to handle --help"""
    # TODO: show venv-update's version on -V/--version
    if set(args) & set(('-h', '--help')):
        print(__doc__, end='')
        exit(0)


def timid_relpath(arg):
    """convert an argument to a relative path, carefully"""
    # TODO-TEST: unit tests
    from os.path import isabs, relpath, sep
    if isabs(arg):
        result = relpath(arg)
        if result.count(sep) + 1 < arg.count(sep):
            return result

    return arg


def shellescape(args):
    from pipes import quote
    return ' '.join(quote(timid_relpath(arg)) for arg in args)


def colorize(cmd):
    from os import isatty

    if isatty(1):
        template = '\033[36m>\033[m \033[32m{0}\033[m'
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


def check_output(cmd):
    from subprocess import Popen, PIPE, CalledProcessError
    process = Popen(cmd, stdout=PIPE)
    output, _ = process.communicate()
    if process.returncode:
        raise CalledProcessError(process.returncode, cmd)
    else:
        assert process.returncode == 0
        return output.decode('UTF-8')


def samefile(file1, file2):
    if not exists(file1) or not exists(file2):
        return False
    else:
        from os.path import samefile
        return samefile(file1, file2)


def exec_(argv):  # never returns
    """Wrapper to os.execv which shows the command and runs any atexit handlers (for coverage's sake).
    Like os.execv, this function never returns.
    """
    ## info('EXEC' + colorize(argv))  # TODO: debug logging by environment variable

    # in python3, sys.exitfunc has gone away, and atexit._run_exitfuncs seems to be the only pubic-ish interface
    #   https://hg.python.org/cpython/file/3.4/Modules/atexitmodule.c#l289
    import atexit
    atexit._run_exitfuncs()  # pylint:disable=protected-access

    from os import execv
    execv(argv[0], argv)


def exec_scratch_virtualenv(args):
    """
    goals:
        - get any random site-packages off of the pythonpath
        - ensure that virtualenv is always importable
        - ensure that we're not using the interpreter that we may need to delete
        - idempotency: do nothing if the above goals are already met
    """
    scratch = join(user_cache_dir(), 'venv-update', __version__)
    scratch_virtualenv = join(scratch, 'venv')
    python = venv_python(scratch_virtualenv)
    venv_update = join(scratch, 'venv-update')

    if not exists(python) or not exists(venv_update):
        if exists(scratch_virtualenv):
            # The virtualenv directory exists, but either the Python
            # interpreter or the symlink doesn't.
            #
            # We might have crashed in the middle or been partially moved;
            # let's just start over.
            from shutil import rmtree
            rmtree(scratch_virtualenv)

        run(('virtualenv', scratch_virtualenv))
        scratch_python = venv_python(scratch_virtualenv)
        # TODO: do we allow user-defined override of which version of virtualenv to install?
        run((scratch_python, '-m', 'pip.__main__', 'install', 'virtualenv'))

        site_packages = check_output((scratch_python, '-c', 'import distutils.sysconfig as s; print(s.get_python_lib())')).strip()
        venv_update_library = join(site_packages, 'venv_update.py')
        from shutil import copyfile
        copyfile(dotpy(__file__), venv_update_library)

        # create (or update) the symlink to venv_update inside site-packages
        from os import remove, symlink
        from os.path import lexists, relpath
        if lexists(venv_update):
            remove(venv_update)
        symlink(relpath(venv_update_library, scratch), venv_update)

    assert exists(venv_update), venv_update
    if samefile(dotpy(__file__), venv_update):
        # TODO-TEST: the original venv-update's directory was on sys.path (when using symlinking)
        return  # all done!
    else:
        # TODO-TEST: sometimes we would get a stale version of venv-update
        exec_((python, venv_update,) + args)


def get_original_path(venv_path):  # TODO-TEST: a unit test
    """This helps us know whether someone has tried to relocate the virtualenv"""
    return check_output(('sh', '-c', '. %s; printf "$VIRTUAL_ENV"' % venv_executable(venv_path, 'activate')))


def has_system_site_packages(interpreter):
    # TODO: unit-test
    system_site_packages = check_output((
        interpreter,
        '-c',
        # stolen directly from virtualenv's site.py
        """\
import site, os.path
print(
    0
    if os.path.exists(
        os.path.join(os.path.dirname(site.__file__), 'no-global-site-packages.txt')
    ) else
    1
)"""
    ))
    system_site_packages = int(system_site_packages)
    assert system_site_packages in (0, 1)
    return bool(system_site_packages)


def get_python_version(interpreter):
    if not exists(interpreter):
        return None

    cmd = (interpreter, '-c', 'import sys; print(sys.version)')
    return check_output(cmd)


def validate_virtualenv(venv_path, source_python, destination_python, options):
    if (
            samefile(get_original_path(venv_path), venv_path) and
            has_system_site_packages(destination_python) == options.system_site_packages
    ):
        # the destination virtualenv is valid, modulo the python version
        if source_python is None:
            source_python = destination_python
            info('Keeping valid virtualenv from previous run.')
            raise SystemExit(0)  # looks good! we're done here.
        else:
            source_version = get_python_version(source_python)
            destination_version = get_python_version(destination_python)

            if source_version == destination_version:
                info('Keeping valid virtualenv from previous run.')
                raise SystemExit(0)  # looks good! we're done here.

    # TODO: say exactly *why* the venv was invalidated
    info('Removing invalidated virtualenv.')
    run(('rm', '-rf', venv_path))


def ensure_virtualenv(args, return_values):
    """Ensure we have a valid virtualenv."""
    def adjust_options(options, virtualenv_args):
        # TODO-TEST: proper error message with no arguments
        if not virtualenv_args or virtualenv_args[0].startswith('-'):
            virtualenv_args.insert(0, DEFAULT_VIRTUALENV_PATH)
        venv_path = return_values.venv_path = virtualenv_args[0]

        if venv_path == DEFAULT_VIRTUALENV_PATH or options.prompt == '<dirname>':
            from os.path import abspath, basename, dirname
            options.prompt = '(%s)' % basename(dirname(abspath(venv_path)))

        return_values.pip_options = tuple(virtualenv_args[1:])
        if not return_values.pip_options:
            return_values.pip_options = ('-r', 'requirements.txt')
        del virtualenv_args[1:]
        # end of option munging.

        # there are (potentially) *three* python interpreters involved here:
        # 1) the interpreter we're currently using
        from sys import executable as current_python
        # 2) the interpreter we're instructing virtualenv to copy
        if options.python is None:
            source_python = None
        else:
            source_python = virtualenv.resolve_interpreter(options.python)
        # 3) the interpreter virtualenv will create
        destination_python = venv_python(venv_path)

        if options.clear and exists(destination_python):  # the implementation in virtualenv is bogus.
            run(('rm', '-rf', venv_path))

        if exists(destination_python):
            validate_virtualenv(venv_path, source_python, destination_python, options)

        if source_python is None:
            source_python = current_python

        if not samefile(current_python, source_python):
            print('re-executing under %s' % timid_relpath(source_python))
            exec_((source_python, dotpy(__file__)) + args)  # never returns

    # this is actually a documented extension point:
    #   http://virtualenv.readthedocs.org/en/latest/reference.html#adjust_options
    import virtualenv
    virtualenv.adjust_options = adjust_options

    info(colorize(('virtualenv',) + args))
    raise_on_failure(virtualenv.main)


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


def touch(filename, timestamp):
    """set the mtime of a file"""
    if timestamp is not None:
        timestamp = (timestamp, timestamp)  # atime, mtime

    from os import utime
    utime(filename, timestamp)


def mark_venv_valid(venv_path):
    wait_for_all_subprocesses()
    touch(venv_path, None)


def mark_venv_invalid(venv_path):
    # LBYL, to attempt to avoid any exception during exception handling
    from os.path import isdir
    if venv_path and isdir(venv_path):
        info('')
        info("Something went wrong! Sending '%s' back in time, so make knows it's invalid." % timid_relpath(venv_path))
        wait_for_all_subprocesses()
        touch(venv_path, 0)


def dotpy(filename):
    if filename.endswith(('.pyc', '.pyo', '.pyd')):
        return filename[:-1]
    else:
        return filename


def venv_executable(venv_path, executable):
    return join(venv_path, 'bin', executable)


def venv_python(venv_path):
    return venv_executable(venv_path, 'python')


def user_cache_dir():
    # stolen from pip.utils.appdirs.user_cache_dir
    from os import getenv
    from os.path import expanduser
    return getenv('XDG_CACHE_HOME', expanduser('~/.cache'))


class CacheOpts(object):

    def __init__(self):
        # We put the cache in the directory that pip already uses.
        # This has better security characteristics than a machine-wide cache, and is a
        #   pattern people can use for open-source projects
        self.pipdir = user_cache_dir() + '/pip-faster'
        # We could combine these caches to one directory, but pip would search everything twice, going slower.
        self.wheelhouse = self.pipdir + '/wheelhouse'

        self.pip_options = (
            '--find-links=file://' + self.wheelhouse,
        )


def venv_update(args):
    """we have an arbitrary python interpreter active, (possibly) outside the virtualenv we want.

    make a fresh venv at the right spot, make sure it has pip-faster, and use it
    """
    exec_scratch_virtualenv(args)
    # invariant: virtualenv (the library) is importable
    # invariant: we're not currently using the destination python

    # SMELL: mutable argument as return value
    class return_values(object):
        venv_path = None
        pip_options = None

    try:
        ensure_virtualenv(args, return_values)
        if return_values.venv_path is None:
            return
        # invariant: the final virtualenv exists, with the right python version
        raise_on_failure(lambda: pip_faster(return_values.venv_path, return_values.pip_options))
    except BaseException:
        mark_venv_invalid(return_values.venv_path)
        raise
    else:
        mark_venv_valid(return_values.venv_path)


def pip_faster(venv_path, pip_options):
    """install and run pip-faster"""
    python = venv_python(venv_path)
    if not exists(python):
        return 'virtualenv executable not found: %s' % python

    pip_install = (python, '-m', 'pip.__main__', 'install') + CacheOpts().pip_options

    if exists(VENV_UPDATE_REQS_OVERRIDE):
        args = ('-r', VENV_UPDATE_REQS_OVERRIDE)
    else:
        args = ('pip-faster==' + __version__,)

    # disable a useless warning
    # FIXME: ensure a "true SSLContext" is available
    from os import environ
    environ['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'

    # TODO: short-circuit when pip-faster is already there.
    run(pip_install + args)
    run((python, '-m', 'pip_faster', 'install', '--prune', '--upgrade') + pip_options)


def raise_on_failure(mainfunc):
    """raise if and only if mainfunc fails"""
    from subprocess import CalledProcessError
    try:
        errors = mainfunc()
        if errors:
            exit(errors)
    except CalledProcessError as error:
        exit(error.returncode)
    except SystemExit as error:
        if error.code:
            raise
    except KeyboardInterrupt:  # I don't plan to test-cover this.  :pragma:nocover:
        exit(1)


def main():
    from sys import argv
    args = tuple(argv[1:])
    parseargs(args)
    return venv_update(args)


if __name__ == '__main__':
    exit(main())
