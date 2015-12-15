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
from pip.exceptions import InstallationError
from pip.index import BestVersionAlreadyInstalled
from pip.index import PackageFinder
from pip.wheel import WheelBuilder

from venv_update import colorize
from venv_update import raise_on_failure
from venv_update import timid_relpath

if True:  # :pragma:nocover:pylint:disable=using-constant-test
    # Debian de-vendorizes the version of pip it ships
    try:
        from pip._vendor import pkg_resources
    except ImportError:
        import pkg_resources


def ignorecase_glob(glob):
    return ''.join([
        '[%s%s]' % (char.lower(), char.upper())
        if char.isalpha() else
        char
        for char in glob
    ])


def optimistic_wheel_search(req, find_links):
    from os.path import join, exists

    best_version = pkg_resources.parse_version('')
    best_link = None
    for findlink in find_links:
        if findlink.startswith('file:'):
            findlink = findlink[5:]
        elif not exists(findlink):
            assert False, 'findlink not file: coverage: %r' % findlink
            continue  # TODO: test coverage
        # this matches the name-munging done in pip.wheel:
        reqname = req.name.replace('-', '_')

        reqname = ignorecase_glob(reqname)
        reqname = join(findlink, reqname + '-*.whl')
        logger.debug('wheel glob: %s', reqname)
        from glob import glob
        for link in glob(reqname):
            from pip.index import Link
            link = Link('file://' + link)
            from pip.wheel import Wheel
            wheel = Wheel(link.filename)
            logger.debug('Candidate wheel: %s', link.filename)
            if wheel.version not in req.req:
                continue

            if not wheel.supported():
                continue

            version = pkg_resources.parse_version(wheel.version)
            if version > best_version:
                best_version = version
                best_link = link

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
                logger.notify('Faster! pinned requirement already installed.')
                raise BestVersionAlreadyInstalled

            # then try an optimistic search for a .whl file:
            link = optimistic_wheel_search(req, self.find_links)
            if link is None:
                logger.notify('SLOW!! no wheel found for pinned requirement %s', req)
            else:
                logger.notify('Faster! Pinned wheel found, without hitting PyPI.')
                return link
        else:
            logger.info('slow: full search for unpinned requirement %s', req)

        # otherwise, do the full network search, per usual
        return super(FasterPackageFinder, self).find_requirement(req, upgrade)
        # TODO: optimization -- do optimisitic wheel search even for unpinned reqs


class FasterWheelBuilder(WheelBuilder):

    def build(self):
        """This is copy-paasta of pip.wheel.Wheelbuilder.build except in the two noted spots"""
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
    return patched(vars(install), {'PackageFinder': FasterPackageFinder})


def pipfaster_install():
    # pip<6 needs this exact import -- they clobber `commands` in __init__
    from pip.commands import install
    return patched(vars(install), {'RequirementSet': FasterRequirementSet})


def pip(args):
    """Run pip, in-process."""
    # pip<1.6 needs its logging config reset on each invocation, or else we get duplicate outputs -.-
    pipmodule.logger.consumers = []

    from sys import stdout
    stdout.write(colorize(('pip',) + args))
    stdout.write('\n')
    stdout.flush()

    # TODO: we probably can do bettter than calling pipmodule.main() now.
    return pipmodule.main(list(args))


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


def fresh_working_set():
    """return a pkg_resources "working set", representing the *currently* installed packages"""
    class WorkingSetPlusEditableInstalls(pkg_resources.WorkingSet):

        def add_entry(self, entry):
            """Same as the original .add_entry, but sets only=False, so that egg-links are honored."""
            logger.debug('working-set entry: %r', entry)
            self.entry_keys.setdefault(entry, [])
            self.entries.append(entry)
            for dist in pkg_resources.find_distributions(entry, False):

                # eggs override anything that's installed normally
                # fun fact: pkg_resources.working_set's results depend on the
                # ordering of os.listdir since the order of os.listdir is
                # entirely arbitrary (an implemenation detail of file system),
                # without calling site.main(), an .egg-link file may or may not
                # be honored, depending on the filesystem
                replace = (dist.precedence == pkg_resources.EGG_DIST)
                self.add(dist, entry, False, replace=replace)

    return WorkingSetPlusEditableInstalls()


def pretty_req(req):
    """
    a context that makes the str() of a pip requirement a bit more readable,
    at the expense of munging its data temporarily
    """
    return patched(vars(req), {'url': None, 'satisfied_by': None})


def trace_requirements(requirements):
    """given an iterable of pip InstallRequirements,
    return the set of required packages, given their transitive requirements.
    """
    working_set = fresh_working_set()

    # breadth-first traversal:
    from collections import deque
    queue = deque(requirements)
    errors = set()
    result = []
    while queue:
        req = queue.popleft()
        logger.debug('tracing: %s', req)

        try:
            dist = working_set.find(req.req)
        except pkg_resources.VersionConflict as conflict:
            dist = conflict.args[0]
            with pretty_req(req):
                errors.add('Error: version conflict: %s (%s) <-> %s' % (
                    dist, timid_relpath(dist.location), req
                ))

        if dist is None:
            errors.add('Error: unmet dependency: %s' % req)
            continue

        result.append(dist_to_req(dist))

        for dist_req in sorted(dist.requires(), key=lambda req: req.key):
            # there really shouldn't be any circular dependencies...
            # temporarily shorten the str(req)
            with pretty_req(req):
                from pip.req import InstallRequirement
                dist_req = InstallRequirement(dist_req, str(req))

            logger.debug('adding sub-requirement %s', dist_req)
            queue.append(dist_req)

    if errors:
        raise InstallationError('\n'.join(sorted(errors)))

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
        wheel_dir = CacheOpts().pip_wheels
        self.wheel_download_dir = wheel_dir

        super(FasterRequirementSet, self).prepare_files(finder, **kwargs)

        # build wheels before install.
        wb = FasterWheelBuilder(
            self,
            finder,
            wheel_dir=wheel_dir,
        )
        # Ignore the result: a failed wheel will be
        # installed from the sdist/vcs whatever.
        # TODO-TEST: we only incur the build cost once on uncached install
        wb.build()

        for req in self.requirements.values():
            if req.is_wheel or req.source_dir is None or req.editable:
                continue

            link = optimistic_wheel_search(req, finder.find_links)
            if link is None:
                logger.notify('SLOW!! No wheel found for %s', req)
                continue

            # replace the setup.py "sdist" with the wheel "bdist"
            from pip.util import rmtree, unzip_file
            rmtree(req.source_dir)
            unzip_file(link.path, req.source_dir, flatten=False)
            req.url = link.url


# TODO: a pip_faster.patch module


def patch(attrs, updates):
    """Perform a set of updates to a attribute dictionary, return the original values."""
    orig = {}
    for attr, value in updates:
        orig[attr] = attrs[attr]
        attrs[attr] = value
    return orig


@contextmanager
def patched(attrs, updates):
    """A context in which some attributes temporarily have a modified value."""
    orig = patch(attrs, updates.items())
    try:
        yield orig
    finally:
        patch(attrs, orig.items())
# END: pip_faster.patch module


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

        # from pip.commands.wheel: make the wheelhouse
        import os.path
        if not os.path.exists(cache_opts.pip_wheels):
            os.makedirs(cache_opts.pip_wheels)

        # from pip.commands.install
        do_install = (not options.no_install and not self.bundle)
        do_prune = do_install and options.prune
        if do_prune:
            previously_installed = pip_get_installed()

        requirement_set = super(FasterInstallCommand, self).run(options, args)

        if requirement_set is None:
            required = ()
            successfully_installed = ()
        else:
            required = requirement_set.requirements.values()
            successfully_installed = requirement_set.successfully_installed

        # transitive requirements, previously installed, are also required
        # this has a side-effect of finding any missing / conflicting requirements
        required = trace_requirements(required)

        if not do_prune:
            return requirement_set

        extraneous = (
            reqnames(previously_installed) -
            reqnames(required) -
            reqnames(successfully_installed) -
            # TODO: instead of this, add `pip-faster` to the `required`, and let trace-requirements do its work
            set(['pip-faster', 'virtualenv', 'pip', 'setuptools', 'wheel', 'argparse'])  # the stage1 bootstrap packages
        )

        if extraneous:
            extraneous = sorted(extraneous)
            pip(('uninstall', '--yes') + tuple(extraneous))

        # TODO: Cleanup: remove stale values from the cache and wheelhouse that have not been accessed in a week.


def pipfaster_install_prune_option():
    return patched(pipmodule.commands, {FasterInstallCommand.name: FasterInstallCommand})


def improved_wheel_support():
    """get the wheel supported-tags from wheel, rather than vendor"""
    import pip.pep425tags
    from wheel.pep425tags import get_supported
    return patched(vars(pip.pep425tags), {
        'supported_tags': get_supported(),
    })


def main():
    with pipfaster_install_prune_option():
        with pipfaster_packagefinder():
            with pipfaster_install():
                with improved_wheel_support():
                    raise_on_failure(pipmodule.main)


if __name__ == '__main__':
    exit(main())
