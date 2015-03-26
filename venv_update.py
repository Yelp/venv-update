#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''\
usage: venv-update [-h] [virtualenv_dir] [requirements [requirements ...]]

Update a (possibly non-existant) virtualenv directory using a requirements.txt listing
When this script completes, the virtualenv should have the same packages as if it were
removed, then rebuilt.

To set the index server, export a PIP_INDEX_SERVER variable.
    See also: http://pip.readthedocs.org/en/latest/user_guide.html#environment-variables

positional arguments:
  virtualenv_dir  Destination virtualenv directory (default: virtualenv_run)
  requirements    Requirements files. (default: requirements.txt)

optional arguments:
  -h, --help      show this help message and exit

Version control at: https://github.com/yelp/venv-update
'''
from __future__ import print_function
from __future__ import unicode_literals

# This script must not rely on anything other than
#   stdlib>=2.6 and virtualenv>1.11
from contextlib import contextmanager

# TODO: provide a way for projects to pin their own versions of wheel
#       probably ./requirements.d/venv-update.txt
BOOTSTRAP_VERSIONS = (
    'wheel==0.24.0',
)


def parseargs(args):
    if set(args) & set(('-h', '--help')):
        print(__doc__, end='')
        exit(0)

    args = list(args)
    stage = 1
    while '--stage2' in args:
        stage = 2
        args.remove('--stage2')

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

    return stage, virtualenv_dir, tuple(requirements), tuple(remaining)


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


def req_is_absolute(requirement):
    if not requirement:
        # url-style requirement
        return False

    for qualifier, dummy_version in requirement.specs:
        if qualifier == '==':
            return True
    return False


def faster_find_requirement(self, req, upgrade):
    """see faster_pip_packagefinder"""
    from pip.index import BestVersionAlreadyInstalled
    if req_is_absolute(req.req):
        # if the version is pinned-down by a ==
        # first try to use any installed package that satisfies the req
        if req.satisfied_by:
            if upgrade:
                # as a matter of api, find_requirement() only raises during upgrade -- shrug
                raise BestVersionAlreadyInstalled
            else:
                return None

        # then try an optimistic search for a .whl file:
        from os.path import join
        from glob import glob
        from pip.wheel import Wheel
        from pip.index import Link
        for findlink in self.find_links:
            if findlink.startswith('file://'):
                findlink = findlink[7:]
            else:
                continue
            # this matches the name-munging done in pip.wheel:
            reqname = req.name.replace('-', '_')
            for link in glob(join(findlink, reqname + '-*.whl')):
                link = Link('file://' + link)
                wheel = Wheel(link.filename)
                if wheel.version in req.req and wheel.supported():
                    return link

    # otherwise, do the full network search
    return self.unpatched['find_requirement'](self, req, upgrade)


@contextmanager
def faster_pip_packagefinder():
    """Provide a short-circuited search when the requirement is pinned and appears on disk.

    Suggested upstream at: https://github.com/pypa/pip/pull/2114
    """
    # A poor man's dependency injection: monkeypatch :(
    # pylint:disable=protected-access
    from pip.index import PackageFinder

    PackageFinder.unpatched = vars(PackageFinder).copy()
    PackageFinder.find_requirement = faster_find_requirement
    try:
        yield
    finally:
        PackageFinder.find_requirement = PackageFinder.unpatched['find_requirement']
        del PackageFinder.unpatched


def pip(args):
    """Run pip, in-process."""
    import pip as pipmodule

    # pip<1.6 needs its logging config reset on each invocation, or else we get duplicate outputs -.-
    pipmodule.logger.consumers = []

    from sys import stdout
    stdout.write(colorize(('pip',) + args))
    stdout.write('\n')
    stdout.flush()

    with faster_pip_packagefinder():
        result = pipmodule.main(list(args))

    if result != 0:
        # pip exited with failure, then we should too
        exit(result)


def dist_to_req(dist):
    """Make a pip.FrozenRequirement from a pkg_resources distribution object"""
    from pip import FrozenRequirement

    # normalize the casing, dashes in the req name
    orig_name, dist.project_name = dist.project_name, dist.key
    result = FrozenRequirement.from_dist(dist, [])
    # put things back the way we found it.
    dist.project_name = orig_name

    return result


def pip_get_installed():
    """Code extracted from the middle of the pip freeze command.
    """
    if True:
        # pragma:no cover:pylint:disable=no-name-in-module,import-error
        try:
            from pip.utils import dist_is_local
        except ImportError:
            # pip < 6.0
            from pip.util import dist_is_local

    return tuple(
        dist_to_req(dist)
        for dist in fresh_working_set()
        if dist_is_local(dist)
    )


def pip_parse_requirements(requirement_files):
    from pip.req import parse_requirements

    # ordering matters =/
    required = []
    for reqfile in requirement_files:
        for req in parse_requirements(reqfile):
            required.append(req)
    return required


def importlib_invalidate_caches():
    """importlib.invalidate_caches is necessary if anything has been installed after python startup.
    New in python3.3.
    """
    try:
        import importlib
    except ImportError:
        return
    invalidate_caches = getattr(importlib, 'invalidate_caches', lambda: None)
    invalidate_caches()


def pip_install(args):
    """Run pip install, and return the set of packages installed.
    """
    from pip.commands.install import InstallCommand

    orig_installcommand = vars(InstallCommand).copy()

    class _nonlocal(object):
        successfully_installed = None

    def install(self, options, args):
        """capture the list of successfully installed packages as they pass through"""
        result = orig_installcommand['run'](self, options, args)
        _nonlocal.successfully_installed = result
        return result

    # A poor man's dependency injection: monkeypatch :(
    InstallCommand.run = install
    try:
        pip(('install',) + args)
    finally:
        InstallCommand.run = orig_installcommand['run']

    # make sure the just-installed stuff is visible to this process.
    importlib_invalidate_caches()

    if _nonlocal.successfully_installed is None:
        return []
    else:
        return _nonlocal.successfully_installed.requirements.values()


def fresh_working_set():
    """return a pkg_resources "working set", representing the *currently* installed pacakges"""
    from pip._vendor import pkg_resources

    class WorkingSetPlusEditableInstalls(pkg_resources.WorkingSet):
        def add_entry(self, entry):
            """Same as the original .add_entry, but sets only=False, so that egg-links are honored."""
            self.entry_keys.setdefault(entry, [])
            self.entries.append(entry)
            for dist in pkg_resources.find_distributions(entry, False):
                self.add(dist, entry, False)

    return WorkingSetPlusEditableInstalls()


def trace_requirements(requirements):
    """given an iterable of pip InstallRequirements,
    return the set of required packages, given their transitive requirements.
    """
    from collections import deque
    from pip import logger
    from pip.req import InstallRequirement
    from pip._vendor import pkg_resources

    working_set = fresh_working_set()

    # breadth-first traversal:
    errors = False
    queue = deque(requirements)
    result = []
    seen_warnings = set()
    while queue:
        req = queue.popleft()
        if req.req is None:
            # a file:/// requirement
            continue

        try:
            dist = working_set.find(req.req)
        except pkg_resources.VersionConflict as conflict:
            dist = conflict.args[0]
            if req.name not in seen_warnings:
                logger.error("Error: version conflict: %s <-> %s" % (dist, req))
                errors = True
                seen_warnings.add(req.name)

        if dist is None:
            logger.error('Error: unmet dependency: %s' % req)
            errors = True
            continue

        result.append(dist_to_req(dist))

        for dist_req in sorted(dist.requires(), key=lambda req: req.key):
            # there really shouldn't be any circular dependencies...
            queue.append(InstallRequirement(dist_req, str(req)))

    if errors:
        exit(1)

    return result


def reqnames(reqs):
    return set(req.name for req in reqs)


def path_is_within(path, within):
    from os.path import relpath, join
    path = join('.', path)  # eliminate empty-string edge case
    return not relpath(path, within).startswith('..')


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


def do_install(reqs):
    from os import environ

    previously_installed = pip_get_installed()
    required = pip_parse_requirements(reqs)

    requirements_as_options = tuple(
        '--requirement={0}'.format(requirement) for requirement in reqs
    )

    # We put the cache in the directory that pip already uses.
    # This has better security characteristics than a machine-wide cache, and is a
    #   pattern people can use for open-source projects
    pipdir = environ['HOME'] + '/.pip'
    # We could combine these caches to one directory, but pip would search everything twice, going slower.
    pip_download_cache = pipdir + '/cache'
    pip_wheels = pipdir + '/wheelhouse'

    environ.update(
        PIP_DOWNLOAD_CACHE=pip_download_cache,
    )

    cache_opts = (
        '--download-cache=' + pip_download_cache,
        '--find-links=file://' + pip_wheels,
    )

    # --use-wheel is somewhat redundant here, but it means we get an error if we have a bad version of pip/setuptools.
    install_opts = ('--upgrade', '--use-wheel',) + cache_opts
    recently_installed = []

    # 1) Bootstrap the install system; setuptools and pip are already installed, just need wheel
    recently_installed += pip_install(install_opts + BOOTSTRAP_VERSIONS)

    # 2) Caching: Make sure everything we want is downloaded, cached, and has a wheel.
    pip(
        ('wheel', '--wheel-dir=' + pip_wheels) +
        BOOTSTRAP_VERSIONS +
        cache_opts +
        requirements_as_options
    )

    # 3) Install: Use our well-populated cache, to do the installations.
    install_opts += ('--no-index',)  # only use the cache
    recently_installed += pip_install(install_opts + requirements_as_options)

    required_with_deps = trace_requirements(required)

    # TODO-TEST require A==1 then A==2
    extraneous = (
        reqnames(previously_installed) -
        reqnames(required_with_deps) -
        reqnames(recently_installed) -
        set(['pip', 'setuptools', 'wheel'])  # the stage1 bootstrap packages
    )

    # 2) Uninstall any extraneous packages.
    if extraneous:
        pip(('uninstall', '--yes') + tuple(sorted(extraneous)))


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
        info("Waiting for all subprocesses to finish...")
        wait_for_all_subprocesses()
        info("DONE")
        backintime(reqs[0], venv_path)
        info('')


def dotpy(filename):
    if filename.endswith(('.pyc', '.pyo', '.pyd')):
        return filename[:-1]
    else:
        return filename


def venv_python(venv_path):
    from os.path import join
    return join(venv_path, 'bin', 'python')


def exec_(argv):
    """Wrapper to os.execv which shows the command and runs any atexit handlers (for coverage's sake).
    Like os.execv, this function never returns.
    """
    info(colorize(argv))

    # in python3, sys.exitfunc has gone away, and atexit._run_exitfuncs seems to be the only pubic-ish interface
    #   https://hg.python.org/cpython/file/3.4/Modules/atexitmodule.c#l289
    import atexit
    atexit._run_exitfuncs()  # pylint:disable=protected-access

    from os import execv
    execv(argv[0], argv)  # never returns


def stage1(venv_path, reqs):
    """we have an arbitrary python interpreter active, (possibly) outside the virtualenv we want.

    make a fresh venv at the right spot, and use it to perform stage 2
    """
    from os.path import exists
    python = venv_python(venv_path)
    if not exists(python):
        return 'virtualenv executable not found: %s' % python

    # ensure that a compatible version of pip is installed
    run(('pip', '--version'))
    run((python, '-m', 'pip.__main__', 'install', 'pip>=1.5.0,<6.0.0'))

    exec_((python, dotpy(__file__), '--stage2', venv_path) + reqs)  # never returns


def stage2(venv_path, reqs):
    """we're activated into the venv we want, and there should be nothing but pip and setuptools installed.
    """
    python = venv_python(venv_path)
    import sys
    assert sys.executable == python, "Executable not in venv: %s != %s" % (sys.executable, python)
    return do_install(reqs)


def venv_update(stage, venv_path, reqs, venv_args):
    from os.path import abspath
    venv_path = abspath(venv_path)
    if stage == 1:
        validate_venv(venv_path, venv_args)
        return stage1(venv_path, reqs)
    elif stage == 2:
        return stage2(venv_path, reqs)
    else:
        raise AssertionError('impossible stage value: %r' % stage)


def main():
    from sys import argv, path
    del path[:1]  # we don't (want to) import anything from pwd or the script's directory
    stage, venv_path, reqs, venv_args = parseargs(argv[1:])

    from subprocess import CalledProcessError
    try:
        return venv_update(stage, venv_path, reqs, venv_args)
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
