#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''pip-faster is a thin wrapper around pip.

It only adds a --prune option to the `install` subcommand.
`pip-faster install --prune` will *uninstall* any installed packages that are
not required.

Otherwise, you should find that pip-faster gives the same results as pip, just
more quickly, especially in the case of pinned requirements (e.g.
package-x==1.2.3).

Version control at: https://github.com/yelp/venv-update
'''
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import errno
import glob
import os
import random
import shutil
import sys
from contextlib import contextmanager

import pip as pipmodule
from pip import logger
from pip.commands.install import InstallCommand
from pip.exceptions import DistributionNotFound
from pip.exceptions import InstallationError
from pip.index import BestVersionAlreadyInstalled
from pip.index import HTMLPage
from pip.index import Link
from pip.index import PackageFinder
from pip.req import InstallRequirement
from pip.wheel import Wheel

from venv_update import colorize
from venv_update import raise_on_failure
from venv_update import timid_relpath
from venv_update import user_cache_dir

if True:  # :pragma:nocover:pylint:disable=using-constant-test
    # Debian de-vendorizes the version of pip it ships
    try:
        # pylint:disable=ungrouped-imports
        from pip._vendor import pkg_resources
    except ImportError:
        import pkg_resources


# Thanks six!
PY2 = str is bytes
if PY2:  # :pragma:nocover:
    _reraise_src = 'def reraise(tp, value, tb=None): raise tp, value, tb'
    exec(_reraise_src)  # pylint:disable=exec-used
else:  # :pragma:nocover:
    def reraise(tp, value, tb=None):  # pylint:disable=invalid-name
        if value is None:
            value = tp()
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value


class CACHE(object):
    _cache_dir = user_cache_dir()
    wheelhouse = os.path.join(_cache_dir, 'pip-faster', 'wheelhouse')
    pip_wheelhouse = os.path.join(_cache_dir, 'pip', 'wheels')


def ignorecase_glob(glob):
    return ''.join([
        '[{0}{1}]'.format(char.lower(), char.upper())
        if char.isalpha() else char
        for char in glob
    ])


def optimistic_wheel_search(req, index_urls):
    name = req.name.replace('-', '_').lower()

    for index_url in index_urls:
        expected_location = os.path.join(
            CACHE.wheelhouse, index_url, ignorecase_glob(name) + '-*.whl',
        )
        for link in glob.glob(expected_location):
            link = Link('file:' + link)
            wheel = Wheel(link.filename)
            if req.specifier.contains(wheel.version) and wheel.supported():
                return link


def is_req_pinned(requirement):
    if not requirement:
        # url-style requirement
        return False

    for spec in requirement.specifier:
        if spec.operator == '==':
            return True
    return False


class FasterPackageFinder(PackageFinder):

    def find_requirement(self, req, upgrade):
        if is_req_pinned(req.req):
            # if the version is pinned-down by a ==
            # first try to use any installed package that satisfies the req
            if req.satisfied_by:
                logger.info('Faster! pinned requirement already installed.')
                raise BestVersionAlreadyInstalled

            # then try an optimistic search for a .whl file:
            link = optimistic_wheel_search(req.req, self.index_urls)
            if link is None:
                # The wheel will be built during prepare_files
                logger.debug('No wheel found locally for pinned requirement %s', req)
            else:
                logger.info('Faster! Pinned wheel found, without hitting PyPI.')
                return link
        else:
            # unpinned requirements aren't very notable. only show with -v
            logger.info('slow: full search for unpinned requirement %s', req)

        # otherwise, do the full network search, per usual
        try:
            return super(FasterPackageFinder, self).find_requirement(req, upgrade)
        except DistributionNotFound:
            exc_info = sys.exc_info()
            # Best effort: try and install from suitable version on-disk
            link = optimistic_wheel_search(req.req, self.index_urls)
            if link:
                return link
            else:
                reraise(*exc_info)


def _can_be_cached(package):
    return (
        package.is_wheel and
        # An assertion that we're looking in the pip wheel dir
        package.link.path.startswith(CACHE.pip_wheelhouse)
    )


def mkdirp(pth):
    try:
        os.makedirs(pth)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def _store_wheel_in_cache(file_path, index_url):
    filename = os.path.basename(file_path)
    cache = os.path.join(CACHE.wheelhouse, index_url, filename)
    cache_tmp = '{0}.{1}'.format(cache, random.randint(0, sys.maxsize))
    cache_dir = os.path.dirname(cache)
    mkdirp(cache_dir)
    # Atomicity
    shutil.copy(file_path, cache_tmp)
    os.rename(cache_tmp, cache)


def cache_installed_wheels(index_url, installed_packages):
    """After installation, pip tells us what it installed and from where.

    We build a structure that looks like

    .cache/pip-faster/wheelhouse/$index_url/$wheel
    """
    for installed_package in installed_packages:
        if not _can_be_cached(installed_package):
            continue
        _store_wheel_in_cache(installed_package.link.path, index_url)


def get_patched_download_http_url(orig_download_http_url, index_url):
    def pipfaster_download_http_url(link, session, temp_dir, hashes):
        file_path, content_type = orig_download_http_url(
            link, session, temp_dir, hashes,
        )
        if (
                link.is_wheel and
                isinstance(link.comes_from, HTMLPage) and
                link.comes_from.url.startswith(index_url)
        ):
            _store_wheel_in_cache(file_path, index_url)
        return file_path, content_type
    return pipfaster_download_http_url


def pip(args):
    """Run pip, in-process."""
    from sys import stdout
    stdout.write(colorize(('pip',) + args))
    stdout.write('\n')
    stdout.flush()

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
    from pip.utils import dist_is_local

    return tuple(
        dist_to_req(dist)
        for dist in fresh_working_set()
        if dist_is_local(dist)
    )


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


def req_cycle(req):
    """is this requirement cyclic?"""
    cls = req.__class__
    seen = set([req.name])
    while isinstance(req.comes_from, cls):
        req = req.comes_from
        if req.name in seen:
            return True
        else:
            seen.add(req.name)
    return False


def pretty_req(req):
    """
    return a copy of a pip requirement that is a bit more readable,
    at the expense of removing some of its data
    """
    from copy import copy
    req = copy(req)
    req.link = None
    req.satisfied_by = None
    return req


def _package_req_to_pkg_resources_req(req):
    return pkg_resources.Requirement.parse(str(req))


def trace_requirements(requirements):
    """given an iterable of pip InstallRequirements,
    return the set of required packages, given their transitive requirements.
    """
    requirements = tuple(pretty_req(r) for r in requirements)
    working_set = fresh_working_set()

    # breadth-first traversal:
    from collections import deque
    queue = deque(requirements)
    queued = set([_package_req_to_pkg_resources_req(req.req) for req in queue])
    errors = []
    result = []
    while queue:
        req = queue.popleft()

        logger.debug('tracing: %s', req)
        try:
            dist = working_set.find(_package_req_to_pkg_resources_req(req.req))
        except pkg_resources.VersionConflict as conflict:
            dist = conflict.args[0]
            errors.append('Error: version conflict: %s (%s) <-> %s' % (
                dist, timid_relpath(dist.location), req
            ))

        assert dist is not None, 'Should be unreachable in pip8+'
        result.append(dist_to_req(dist))

        # TODO: pip does no validation of extras. should we?
        extras = [extra for extra in req.extras if extra in dist.extras]
        for sub_req in sorted(dist.requires(extras=extras), key=lambda req: req.key):
            sub_req = InstallRequirement(sub_req, req)

            if req_cycle(sub_req):
                logger.warning('Circular dependency! %s', sub_req)
                continue
            elif sub_req.req in queued:
                logger.debug('already queued: %s', sub_req)
                continue
            else:
                logger.debug('adding sub-requirement %s', sub_req)
                queue.append(sub_req)
                queued.add(sub_req.req)

    if errors:
        raise InstallationError('\n'.join(errors))

    return result


def reqnames(reqs):
    return set(req.name for req in reqs)


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
        if options.prune:
            previously_installed = pip_get_installed()

        with pipfaster_download_cacher(options.index_url):
            requirement_set = super(FasterInstallCommand, self).run(
                options, args,
            )

        if requirement_set is None:
            required = ()
            successfully_installed = ()
        else:
            required = requirement_set.requirements.values()
            successfully_installed = requirement_set.successfully_installed

        # With extra_index_urls we don't know where the wheel is from
        if not options.extra_index_urls:
            cache_installed_wheels(options.index_url, successfully_installed)

        # transitive requirements, previously installed, are also required
        # this has a side-effect of finding any missing / conflicting requirements
        required = trace_requirements(required)

        if not options.prune:
            return requirement_set

        extraneous = (
            reqnames(previously_installed) -
            reqnames(required) -
            reqnames(successfully_installed) -
            reqnames(trace_requirements([InstallRequirement.from_line('venv-update')]))  # the stage1 bootstrap packages
        )

        if extraneous:
            extraneous = sorted(extraneous)
            pip(('uninstall', '--yes') + tuple(extraneous))

        # TODO: Cleanup: remove stale values from the cache and wheelhouse that have not been accessed in a week.

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


def pipfaster_install_prune_option():
    return patched(pipmodule.commands.commands_dict, {FasterInstallCommand.name: FasterInstallCommand})


def pipfaster_packagefinder():
    """Provide a short-circuited search when the requirement is pinned and appears on disk.

    Suggested upstream at: https://github.com/pypa/pip/pull/2114
    """
    # A poor man's dependency injection: monkeypatch :(
    from pip import basecommand
    return patched(vars(basecommand), {'PackageFinder': FasterPackageFinder})


def pipfaster_download_cacher(index_url):
    """vanilla pip stores a cache of the http session in its cache and not the
    wheel files.  We intercept the download and save those files into our
    cache
    """
    from pip import download
    orig = download._download_http_url  # pylint:disable=protected-access
    patched_fn = get_patched_download_http_url(orig, index_url)
    return patched(vars(download), {'_download_http_url': patched_fn})


def main():
    with pipfaster_install_prune_option():
        with pipfaster_packagefinder():
            raise_on_failure(pipmodule.main)


if __name__ == '__main__':
    exit(main())
