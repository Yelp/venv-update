#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''\
usage: pip-faster [-h] [requirements [requirements ...]]

Update the current environment using a requirements.txt listing
When this script completes, the environment should have the same packages as if it were
removed, then rebuilt.

To set the index server, export a PIP_INDEX_SERVER variable.
    See also: http://pip.readthedocs.org/en/latest/user_guide.html#environment-variables

positional arguments:
  requirements    Requirements files. (default: requirements.txt)

optional arguments:
  -h, --help      show this help message and exit

Version control at: https://github.com/yelp/venv-update
'''
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from contextlib import contextmanager

from venv_update import colorize
from venv_update import parseargs
from venv_update import run
from venv_update import timid_relpath

# TODO: provide a way for projects to pin their own versions of wheel
#       probably ./requirements.d/venv-update.txt
BOOTSTRAP_VERSIONS = (
    'wheel==0.24.0',
)


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
    FIXME: does not list anything installed via -e
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
    try:
        from pip._vendor import pkg_resources
    except ImportError:  # pragma: no cover
        # Debian de-vendorizes the version of pip it ships
        import pkg_resources

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
    try:
        from pip._vendor import pkg_resources
    except ImportError:  # pragma: no cover
        # Debian de-vendorizes the version of pip it ships
        import pkg_resources

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
                # TODO-TEST: conflict with an egg in a directory install via -e ...
                if dist.location:
                    location = ' (%s)' % timid_relpath(dist.location)
                else:
                    location = ''
                logger.error('Error: version conflict: %s%s <-> %s' % (dist, location, req))
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

    # Cleanup: remove stale values from the cache and wheelhouse that have not been accessed in a week.
    from subprocess import CalledProcessError
    try:
        run(['find', pip_download_cache, pip_wheels, '-not', '-atime', '-7', '-delete'])
    except CalledProcessError:  # Ignore errors due to concurrent file access race conditions.
        pass


def main():
    from sys import argv, path
    del path[:1]  # we don't (want to) import anything from pwd or the script's directory
    # TODO: Don't use venv-update's parseargs, instead conform to pip's args
    _, _, reqs, _ = parseargs(argv[1:])

    try:
        return do_install(reqs)
    except SystemExit as error:
        exit_code = error.code
    except KeyboardInterrupt:
        exit_code = 1
    except Exception:
        raise

    return exit_code


if __name__ == '__main__':
    exit(main())
