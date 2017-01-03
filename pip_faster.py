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

from contextlib import contextmanager

import pip as pipmodule
from pip import logger
from pip.commands.install import InstallCommand
from pip.commands.install import RequirementSet
from pip.exceptions import InstallationError
from pip.index import BestVersionAlreadyInstalled
from pip.index import PackageFinder
from pip.utils.logging import indent_log
from pip.wheel import WheelBuilder

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


def ignorecase_glob(glob):
    return ''.join([
        '[%s%s]' % (char.lower(), char.upper())
        if char.isalpha() else
        char
        for char in glob
    ])


def is_local_directory(url):
    """Test if a URL is a directory on this machine.

    >>> is_local_directory('file:///tmp/')
    True
    >>> is_local_directory('file:///etc/passwd')
    False
    >>> is_local_directory('http://yelp.com/')
    False
    >>> is_local_directory('file:.')
    True
    """
    if url is None:
        return False
    elif not url.startswith('file:'):
        return False
    else:
        from os.path import isdir
        return isdir(url[5:])


def is_vcs_url(url):
    """Test if a URL is a VCS repo.

    >>> is_vcs_url('git+git://git.myproject.org/MyProject#egg=MyProject')
    True
    >>> is_vcs_url('svn+http://svn.myproject.org/svn/MyProject/trunk@2019#egg=MyProject')
    True
    >>> is_vcs_url('file:///tmp/')
    False
    """
    if url is None:
        return False
    else:
        return url.startswith(tuple(
            scheme + '+'
            for scheme in pipmodule.vcs.vcs
        ))


def optimistic_wheel_search(req, find_links):
    assert req_is_pinned(req), req

    # this matches the name-munging done in pip.wheel:
    try:
        reqname = req.project_name
    except AttributeError:
        reqname = req.name
    reqname = reqname.replace('-', '_')
    reqname = ignorecase_glob(reqname)
    reqname = reqname + '-*.whl'

    for findlink in find_links:
        if findlink.startswith('file:'):
            findlink = findlink[5:]
        from os.path import join
        findlink = join(findlink, reqname)
        logger.debug('wheel glob: %s', findlink)
        from glob import glob
        for link in glob(findlink):
            from pip.index import Link
            link = Link('file:' + link)
            from pip.wheel import Wheel
            wheel = Wheel(link.filename)
            logger.debug('Candidate wheel: %s', link.filename)
            if req.specifier.contains(wheel.version) and wheel.supported():
                return link


def req_is_pinned(requirement):
    if not requirement:
        # url-style requirement
        return False

    for spec in requirement.specifier:
        if spec.operator == '==':
            return True
    return False


class FasterPackageFinder(PackageFinder):

    def find_requirement(self, req, upgrade):
        if req_is_pinned(req.req):
            # if the version is pinned-down by a ==
            # first try to use any installed package that satisfies the req
            if req.satisfied_by:
                logger.info('Faster! pinned requirement already installed.')
                raise BestVersionAlreadyInstalled

            # then try an optimistic search for a .whl file:
            link = optimistic_wheel_search(req.req, self.find_links)
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
        return super(FasterPackageFinder, self).find_requirement(req, upgrade)
        # Now we know the "best" version, even for unpinned requirements.
        # TODO: optimization -- for unpinned reqs, convert to == and try an optimisitic wheel search


def wheelable(req):
    url = req.link.url if req.link is not None else None
    """do we want to wheel that thing?"""
    return (
        # let's not wheel things that are already installed
        not req.satisfied_by and
        # people expect `pip install .` to work without bumping the version
        not is_local_directory(url) and
        # don't cache vcs packages, since the version is often bogus (#156)
        not is_vcs_url(url)
    )


class FasterWheelBuilder(WheelBuilder):

    def build(self, autobuilding=False):
        """This is copy-paasta of pip.wheel.Wheelbuilder.build except in the spots marked with FASTER"""

        assert self._wheel_dir or (autobuilding and self._cache_root)

        # FASTER: the slower wheelbuilder did self.requirement_set.prepare_files() here
        reqset = self.requirement_set.requirements.values()

        # FASTER: save buildset as instance variable so we can retrieve it later
        self.buildset = []
        for req in reqset:
            if not wheelable(req):
                # FASTER: Skip packages we don't want to wheel
                continue
            if req.constraint:
                continue
            if req.is_wheel:
                if not autobuilding:
                    logger.info(
                        'Skipping %s, due to already being wheel.', req.name)
            elif autobuilding and req.editable:
                pass
            elif autobuilding and req.link and not req.link.is_artifact:
                pass
            elif autobuilding and not req.source_dir:
                pass
            else:
                if autobuilding:
                    link = req.link
                    base, ext = link.splitext()
                    if pip.index.egg_info_matches(base, None, link) is None:
                        # Doesn't look like a package - don't autobuild a wheel
                        # because we'll have no way to lookup the result sanely
                        continue
                    if "binary" not in pip.index.fmt_ctl_formats(
                            self.finder.format_control,
                            canonicalize_name(req.name)):
                        logger.info(
                            "Skipping bdist_wheel for %s, due to binaries "
                            "being disabled for it.", req.name)
                        continue
                self.buildset.append(req)

        if not self.buildset:
            return True

        # Build the wheels.
        logger.info(
            'Building wheels for collected packages: %s',
            ', '.join([req.name for req in self.buildset]),
        )
        with indent_log():
            build_success, build_failure = [], []
            for req in self.buildset:
                python_tag = None
                if autobuilding:
                    python_tag = pep425tags.implementation_tag
                    output_dir = _cache_for_link(self._cache_root, req.link)
                    try:
                        ensure_dir(output_dir)
                    except OSError as e:
                        logger.warning("Building wheel for %s failed: %s",
                                       req.name, e)
                        build_failure.append(req)
                        continue
                else:
                    output_dir = self._wheel_dir
                wheel_file = self._build_one(
                    req, output_dir,
                    python_tag=python_tag,
                )
                if wheel_file:
                    build_success.append(req)
                    if autobuilding:
                        # XXX: This is mildly duplicative with prepare_files,
                        # but not close enough to pull out to a single common
                        # method.
                        # The code below assumes temporary source dirs -
                        # prevent it doing bad things.
                        if req.source_dir and not os.path.exists(os.path.join(
                                req.source_dir, PIP_DELETE_MARKER_FILENAME)):
                            raise AssertionError(
                                "bad source dir - missing marker")
                        # Delete the source we built the wheel from
                        req.remove_temporary_source()
                        # set the build directory again - name is known from
                        # the work prepare_files did.
                        req.source_dir = req.build_location(
                            self.requirement_set.build_dir)
                        # Update the link for this.
                        req.link = pip.index.Link(
                            path_to_url(wheel_file))
                        assert req.link.is_wheel
                        # extract the wheel into the dir
                        unpack_url(
                            req.link, req.source_dir, None, False,
                            session=self.requirement_set.session)
                else:
                    build_failure.append(req)

        # notify success/failure
        if build_success:
            logger.info(
                'Successfully built %s',
                ' '.join([req.name for req in build_success]),
            )
        if build_failure:
            logger.info(
                'Failed to build %s',
                ' '.join([req.name for req in build_failure]),
            )
        # Return True if all builds were successful
        return len(build_failure) == 0


def pipfaster_packagefinder():
    """Provide a short-circuited search when the requirement is pinned and appears on disk.

    Suggested upstream at: https://github.com/pypa/pip/pull/2114
    """
    # A poor man's dependency injection: monkeypatch :(
    # we need this exact import -- pip clobbers `commands` in their __init__
    from pip import basecommand
    return patched(vars(basecommand), {'PackageFinder': FasterPackageFinder})


@contextmanager
def pipfaster_install():
    # pip<6 needs this exact import -- they clobber `commands` in __init__
    from pip.commands import install
    with patched(vars(install), {'RequirementSet': FasterRequirementSet}):
        yield


def pip(args):
    """Run pip, in-process."""
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


def trace_requirements(requirements):
    """given an iterable of pip InstallRequirements,
    return the set of required packages, given their transitive requirements.
    """
    requirements = tuple(pretty_req(r) for r in requirements)
    working_set = fresh_working_set()

    # breadth-first traversal:
    from collections import deque
    queue = deque(requirements)
    queued = set([pkg_resources.Requirement.parse(str(req.req)) for req in queue])
    errors = []
    result = []
    while queue:
        req = queue.popleft()

        logger.debug('tracing: %s', req)
        try:
            # WorkingSet.find needs a pip._vendor.pkg_resorces.Requirement
            # while req is a pip._vendor.packaging.requirements.Requirement
            tmp_req = pkg_resources.Requirement.parse(str(req.req))
            dist = working_set.find(tmp_req)
        except pkg_resources.VersionConflict as conflict:
            dist = conflict.args[0]
            errors.append('Error: version conflict: %s (%s) <-> %s' % (
                dist, timid_relpath(dist.location), req
            ))

        if dist is None:
            errors.append('Error: unmet dependency: %s' % req)
            continue

        result.append(dist_to_req(dist))

        # TODO: pip does no validation of extras. should we?
        extras = [extra for extra in req.extras if extra in dist.extras]
        for sub_req in sorted(dist.requires(extras=extras), key=lambda req: req.key):
            from pip.req import InstallRequirement
            sub_req = InstallRequirement(sub_req, req)

            if req_cycle(sub_req):
                logger.warn('Circular dependency! %s', sub_req)
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


class CacheOpts(object):

    def __init__(self):
        self.pipdir = user_cache_dir() + '/pip-faster'
        self.wheelhouse = self.pipdir + '/wheelhouse'

        self.pip_options = (
            '--find-links=file://' + self.wheelhouse,
        )


class FasterRequirementSet(RequirementSet):

    def prepare_files(self, finder, **kwargs):
        wheel_dir = CacheOpts().wheelhouse
        self.wheel_download_dir = wheel_dir

        super(FasterRequirementSet, self).prepare_files(finder, **kwargs)

        # build wheels before install.
        wb = FasterWheelBuilder(
            self,
            finder,
        )
        wb.build()

        # TODO-TEST: we only incur the build cost once on uncached install
        for req in wb.buildset:
            # Create a pinned req, matching the source we have.
            # We can't convert req (pip.req.req_install.Requirement) to pkg_resources.Requirement
            # directly, we need to regenerate the requirement string instead.
            pinned = pkg_resources.Requirement.parse(req.name + '==' + req.pkg_info()['version'])
            link = optimistic_wheel_search(pinned, finder.find_links)
            if link is None:
                logger.error('SLOW!! no wheel found after building (couldn\'t be wheeled?): %s', pinned)
                continue

            # replace the setup.py "sdist" with the wheel "bdist"
            # from pip.utils import rmtree, unzip_file
            # rmtree(req.source_dir)
            # unzip_file(link.path, req.source_dir, flatten=False)
            # req.url = link.url


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


def reqnames(reqs):
    return set(req.name for req in reqs)


class FasterInstallCommand(InstallCommand):

    def __init__(self, *args, **kw):
        super(FasterInstallCommand, self).__init__(*args, **kw)

        self.cmd_opts.add_option(
            '--prune',
            action='store_true',
            dest='prune',
            default=False,
            help='Uninstall any non-required packages.',
        )

    def run(self, options, args):
        """update install options with caching values"""
        cache_opts = CacheOpts()
        options.find_links.append('file://' + cache_opts.wheelhouse)

        # from pip.commands.wheel: make the wheelhouse
        import os.path
        if not os.path.exists(cache_opts.wheelhouse):
            os.makedirs(cache_opts.wheelhouse)

        if options.prune:
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

        if not options.prune:
            return requirement_set

        extraneous = (
            reqnames(previously_installed) -
            reqnames(required) -
            reqnames(successfully_installed) -
            # TODO: instead of this, add `venv-update` to the `required`, and let trace-requirements do its work
            set(['venv-update', 'virtualenv', 'pip', 'setuptools', 'wheel', 'argparse'])  # the stage1 bootstrap packages
        )

        if extraneous:
            extraneous = sorted(extraneous)
            pip(('uninstall', '--yes') + tuple(extraneous))

        # TODO: Cleanup: remove stale values from the cache and wheelhouse that have not been accessed in a week.


def pipfaster_install_prune_option():
    return patched(pipmodule.commands.commands_dict, {FasterInstallCommand.name: FasterInstallCommand})


def improved_wheel_support():
    """get the wheel supported-tags from wheel, rather than vendor
    This fixes pypy3 support.
    """
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
