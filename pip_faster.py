#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''\
usage: pip-faster [-h] [virtualenv_dir(ignored)] [requirements [requirements ...]]

Update the current environment using a requirements.txt listing
When this script completes, the environment should have the same packages as if it were
removed, then rebuilt.

To set the index server, export a PIP_INDEX_SERVER variable.
    See also: http://pip.readthedocs.org/en/latest/user_guide.html#environment-variables

positional arguments:
  requirements    Requirements files. (default: requirements.txt)

optional arguments:
  -h, --help      show this help message and exit

Version control at: https://github.com/yelp/pip-faster
'''
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from contextlib import contextmanager

import pip as pipmodule
from pip import logger
from pip.commands.install import InstallCommand
from pip.commands.install import RequirementSet
from pip.index import BestVersionAlreadyInstalled
from pip.index import PackageFinder
from pip.wheel import WheelBuilder
from pip.exceptions import InstallationError

from venv_update import colorize
from venv_update import timid_relpath


def optimistic_wheel_search(req, find_links):
    from os.path import join

    best_version = None
    best_link = None
    for findlink in find_links:
        if findlink.startswith('file://'):
            findlink = findlink[7:]
        else:
            continue
        # this matches the name-munging done in pip.wheel:
        reqname = req.name.replace('-', '_')

        def either(char):
            if char.isalpha():
                return '[%s%s]' % (char.lower(), char.upper())
            else:
                return char
        reqname = ''.join([either(c) for c in reqname])
        pattern = join(findlink, reqname + '-*.whl')
        print('WHEELSEARCH:', pattern)
        from glob import glob
        for link in glob(pattern):
            from pip.index import Link
            link = Link('file://' + link)
            from pip.wheel import Wheel
            wheel = Wheel(link.filename)
            print(link.filename)
            if wheel.version not in req.req:
                continue

            if not wheel.supported():
                continue

            from pkg_resources import parse_version
            version = parse_version(wheel.version)
            if version > best_version:
                best_version = version
                best_link = link

    print('WHEELFOUND:', best_link)
    return best_link


def req_is_absolute(requirement):
    if not requirement:
        # url-style requirement
        return False

    for qualifier, dummy_version in requirement.specs:
        if qualifier == '==':
            return True
    return False


class FasterPackageFinder(PackageFinder):

    def find_requirement(self, req, upgrade):
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
            link = optimistic_wheel_search(req, self.find_links)
            if link is not None:
                return link

        # otherwise, do the full network search, per usual
        print('FULL SEARCH FOR', req)
        return super(FasterPackageFinder, self).find_requirement(req, upgrade)
        # TODO: optimization -- do optimisitic wheel search even for unpinned reqs


class FasterWheelBuilder(WheelBuilder):

    def build_one(self, req):
        return self._build_one(req)

    def build(self):
        """This is copy-pasta of pip.wheel.Wheelbuilder.build except in the two noted spots"""
        # TODO-TEST: `pip-faster wheel` works at all
        # FASTER: the slower wheelbuilder did self.requirement_set.prepare_files() here

        reqset = self.requirement_set.requirements.values()

        buildset = [
            req for req in reqset
            # FASTER: don't wheel things that have no source available
            if not req.is_wheel and req.source_dir
        ]

        if not buildset:
            return

        # build the wheels
        logger.notify(
            'Building wheels for collected packages: %s' %
            ','.join([req.name for req in buildset])
        )
        logger.indent += 2
        build_success, build_failure = [], []
        for req in buildset:
            if self._build_one(req):
                build_success.append(req)
            else:
                build_failure.append(req)
        logger.indent -= 2

        # notify sucess/failure
        if build_success:
            logger.notify('Successfully built %s' % ' '.join([req.name for req in build_success]))
        if build_failure:
            logger.notify('Failed to build %s' % ' '.join([req.name for req in build_failure]))


def pipfaster_packagefinder():
    """Provide a short-circuited search when the requirement is pinned and appears on disk.

    Suggested upstream at: https://github.com/pypa/pip/pull/2114
    """
    # A poor man's dependency injection: monkeypatch :(
    # we need this exact import -- pip clobbers `commands` in their __init__
    from pip.commands import install
    return patch(vars(install), {'PackageFinder': FasterPackageFinder})


def pipfaster_install():
    # pip<6 needs this exact import -- they clobber `commands` in __init__
    from pip.commands import install
    return patch(vars(install), {'RequirementSet': FasterRequirementSet})


def pip(args):
    """Run pip, in-process."""
    # pip<1.6 needs its logging config reset on each invocation, or else we get duplicate outputs -.-
    pipmodule.logger.consumers = []

    from sys import stdout
    stdout.write(colorize(('pip',) + args))
    stdout.write('\n')
    stdout.flush()

    result = pipmodule.main(list(args))

    if result:
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
    from pip.req import InstallRequirement
    try:
        from pip._vendor import pkg_resources
    except ImportError:  # pragma: no cover
        # Debian de-vendorizes the version of pip it ships
        import pkg_resources

    working_set = fresh_working_set()

    # breadth-first traversal:
    errors = []
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
                errors.append('Error: version conflict: %s%s <-> %s' % (dist, location, req))
                seen_warnings.add(req.name)

        if dist is None:
            errors.append('Error: unmet dependency: %s' % req)
            continue

        result.append(dist_to_req(dist))

        for dist_req in sorted(dist.requires(), key=lambda req: req.key):
            # there really shouldn't be any circular dependencies...
            # temporarily shorten the str(req)
            with patch(vars(req), {'url': None, 'satisfied_by': None}):
                queue.append(InstallRequirement(dist_req, str(req)))

    if errors:
        raise InstallationError('\n'.join(errors))

    return result


def reqnames(reqs):
    return set(req.name for req in reqs)


class CacheOpts(object):

    def __init__(self):
        from os import environ
        # We put the cache in the directory that pip already uses.
        # This has better security characteristics than a machine-wide cache, and is a
        #   pattern people can use for open-source projects
        self.pipdir = environ['HOME'] + '/.pip'
        # We could combine these caches to one directory, but pip would search everything twice, going slower.
        self.pip_download_cache = self.pipdir + '/cache'
        self.pip_wheels = self.pipdir + '/wheelhouse'

        self.opts = (
            '--download-cache=' + self.pip_download_cache,
            '--find-links=file://' + self.pip_wheels,
        )


class FasterRequirementSet(RequirementSet):
    def prepare_files(self, finder, **kwargs):
        super(FasterRequirementSet, self).prepare_files(finder, **kwargs)

        # build wheels before install.
        wb = FasterWheelBuilder(
            self,
            finder,
            wheel_dir=CacheOpts().pip_wheels,
        )
        # Ignore the result: a failed wheel will be
        # installed from the sdist/vcs whatever.
        # TODO-TEST: we only incur the build cost once on uncached install
        wb.build()

        for req in self.requirements.values():
            if req.is_wheel or req.source_dir is None:
                continue

            link = optimistic_wheel_search(req, finder.find_links)
            if link is None:
                print('WHEEL MISS!')
                continue

            # replace the setup.py "sdist" with the wheel "bdist"
            from pip.util import rmtree, unzip_file
            rmtree(req.source_dir)
            unzip_file(link.path, req.source_dir, flatten=False)
            req.url = link.url

# patch >>>
class Sentinel(str):
    """A named value that only supports the `is` operator."""

    def __repr__(self):
        return '<Sentinel: %s>' % str(self)


def do_patch(attrs, updates):
    """Perform a set of updates to a attribute dictionary, return the original values."""
    orig = {}
    for attr, value in updates:
        orig[attr] = attrs.get(attr, patch.DELETE)
        if value is patch.DELETE:
            del attrs[attr]
        else:
            attrs[attr] = value
    return orig


@contextmanager
def patch(attrs, updates):
    """A context in which some attributes temporarily have a modified value."""
    orig = do_patch(attrs, updates.items())
    yield orig
    do_patch(attrs, orig.items())
patch.DELETE = Sentinel('patch.DELETE')
# patch <<<


class FasterInstallCommand(InstallCommand):

    def __init__(self, *args, **kw):
        super(FasterInstallCommand, self).__init__(*args, **kw)

        cmd_opts = self.cmd_opts
        cmd_opts.add_option(
            '--prune',
            action='store_true',
            dest='prune',
            default=False,
            help='Uninstall any non-required packages.',
        )

        cmd_opts.add_option(
            '--no-prune',
            action='store_false',
            dest='prune',
            help='Do not uninstall any non-required packages.',
        )

    def run(self, options, args):
        """update install options with caching values"""
        cache_opts = CacheOpts()
        options.find_links.append('file://' + cache_opts.pip_wheels)
        options.download_cache = cache_opts.pip_download_cache
        # from pip.commands.install
        do_install = (not options.no_install and not self.bundle)
        do_prune = do_install and options.prune
        if do_prune:
            previously_installed = pip_get_installed()

        requirement_set = super(FasterInstallCommand, self).run(options, args)

        if not do_prune:
            return requirement_set

        if requirement_set is None:
            required = ()
            successfully_installed = ()
        else:
            required = requirement_set.requirements.values()
            successfully_installed = requirement_set.successfully_installed

        # transitive requirements, previously installed, are also required
        required = trace_requirements(required)

        extraneous = (
            reqnames(previously_installed) -
            reqnames(required) -
            reqnames(successfully_installed) -
            # TODO: instead of this, add `pip-faster` to the `required`, and let trace-requirements do its work
            set(['pip-faster', 'pip', 'setuptools', 'wheel', 'argparse'])  # the stage1 bootstrap packages
        )

        if extraneous:
            extraneous = sorted(extraneous)
            pip(('uninstall', '--yes') + tuple(extraneous))

        # TODO: Cleanup: remove stale values from the cache and wheelhouse that have not been accessed in a week.


def pipfaster_install_prune_option():
    return patch(pipmodule.commands, {FasterInstallCommand.name: FasterInstallCommand})


def main():
    with pipfaster_install_prune_option():
        with pipfaster_packagefinder():
            with pipfaster_install():
                try:
                    exit_code = pipmodule.main()
                except SystemExit as error:
                    exit_code = error.code
                except KeyboardInterrupt:
                    exit_code = 1

    return exit_code


if __name__ == '__main__':
    exit(main())
