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


def parseargs(args):
    # TODO: unit test
    if set(args) & set(('-h', '--help')):
        print(__doc__, end='')
        exit(0)

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
    from os.path import exists, isabs, relpath
    if isabs(arg) and exists(arg):
        result = relpath(arg)
        if len(result) < len(arg):
            return result

    return arg


def shellescape(args):
    # TODO: unit test
    from pipes import quote
    return ' '.join(quote(timid_relpath(arg)) for arg in args)


def colorize(cmd):
    from os import isatty

    if isatty(1):
        template = '\033[01;36m>\033[m \033[01;33m{0}\033[m'
    else:
        template = '> {0}'

    return template.format(shellescape(cmd))


def run(cmd):
    from subprocess import check_call
    check_call(('echo', colorize(cmd)))
    check_call(cmd)


@contextmanager
def faster_pip_packagefinder():
    """Provide a short-circuited search when the requirement is pinned and appears on disk.

    Suggested upstream at: https://github.com/pypa/pip/pull/2114
    """
    from pip.index import PackageFinder, DistributionNotFound, HTMLPage

    orig_packagefinder = vars(PackageFinder).copy()

    def find_requirement(self, req, upgrade):
        if any(op == '==' for op, ver in req.req.specs):
            # if the version is pinned-down by a ==, do an optimistic search
            # for a satisfactory package on the local filesystem.
            try:
                self.network_allowed = False
                result = orig_packagefinder['find_requirement'](self, req, upgrade)
            except DistributionNotFound:
                result = None

            if result is not None:
                return result

        # otherwise, do the full network search
        self.network_allowed = True
        return orig_packagefinder['find_requirement'](self, req, upgrade)

    def _get_page(self, link, req):
        if self.network_allowed or link.url.startswith('file:'):
            return orig_packagefinder['_get_page'](self, link, req)
        else:
            return HTMLPage('', 'fake://' + link.url)

    # A poor man's dependency injection: monkeypatch :(
    # pylint:disable=protected-access
    PackageFinder.find_requirement = find_requirement
    PackageFinder._get_page = _get_page
    try:
        yield
    finally:
        PackageFinder.find_requirement = orig_packagefinder['find_requirement']
        PackageFinder._get_page = orig_packagefinder['_get_page']


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


def pip_get_installed():
    """Code extracted from the middle of the pip freeze command.
    """
    from pip import FrozenRequirement
    from pip._vendor.pkg_resources import working_set
    from pip.util import get_installed_distributions

    dependency_links = []

    for dist in working_set:
        if dist.has_metadata('dependency_links.txt'):
            dependency_links.extend(
                dist.get_metadata_lines('dependency_links.txt')
            )

    installed = {}
    for dist in get_installed_distributions(local_only=True):
        req = FrozenRequirement.from_dist(
            dist,
            dependency_links,
        )

        installed[req.name] = req

    return installed


def pip_parse_requirements(requirement_files):
    from pip.req import parse_requirements

    required = {}
    for reqfile in requirement_files:
        for req in parse_requirements(reqfile):
            required[req.name] = req
    return required


def pip_install(args):
    """Run pip install, and return the set of packages installed.
    """
    from sys import stdout
    stdout.write(colorize(('pip', 'install') + args))
    stdout.write('\n')
    stdout.flush()

    from pip.commands.install import InstallCommand
    install = InstallCommand()
    parsed = install.parse_args(list(args))
    successfully_installed = install.run(*parsed)
    if successfully_installed is None:
        return {}
    else:
        return dict(successfully_installed.requirements)


def trace_requirements(requirements):
    """given an iterable of pkg_resources requirements,
    return the set of required packages, given their transitive requirements.
    """
    from pip._vendor.pkg_resources import get_provider, DistributionNotFound

    stack = list(requirements)
    result = {}
    while stack:
        req = stack.pop()
        if req is None:
            # a file:/// requirement
            continue

        try:
            dist = get_provider(req)
        except (DistributionNotFound, IOError):
            result[req.project_name] = None
            continue

        result[dist.project_name] = dist

        for req in dist.requires():  # should we support extras?
            if req.project_name not in result:
                stack.append(req)

    return result


@contextmanager
def venv(venv_path, venv_args):
    """Ensure we have a virtualenv."""
    virtualenv = ('virtualenv', venv_path)
    run(virtualenv + venv_args)

    yield

    # Postprocess: Make our venv relocatable, since we do plan to relocate it, sometimes.
    run(
        virtualenv +
        ('--relocatable', '--python={0}/bin/python'.format(venv_path))
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
    pip_download_cache = environ['HOME'] + '/.pip/cache'

    environ.update(
        PIP_DOWNLOAD_CACHE=pip_download_cache,
    )

    cache_opts = (
        '--download-cache=' + pip_download_cache,
        '--find-links=file://' + pip_download_cache,
    )

    # --use-wheel is somewhat redundant here, but it means we get an error if we have a bad version of pip/setuptools.
    install_opts = ('--use-wheel',) + cache_opts
    wheel = ('wheel',) + cache_opts

    # Bootstrap the install system; setuptools and pip are alreayd installed, just need wheel
    pip_install(install_opts + ('wheel',))

    # Caching: Make sure everything we want is downloaded, cached, and has a wheel.
    pip(wheel + ('--wheel-dir=' + pip_download_cache, 'wheel') + requirements_as_options)

    # Install: Use our well-populated cache (only) to do the installations.
    # The --ignore-installed gives more-repeatable behavior in the face of --system-site-packages,
    #   and brings us closer to a --no-site-packages future
    recently_installed = pip_install(install_opts + ('--upgrade', '--no-index',) + requirements_as_options)

    required_with_deps = trace_requirements(
        (req.req for req in required.values())
    )

    # TODO-TEST require A==1 then A==2
    extraneous = (
        set(previously_installed) -
        set(required_with_deps) -
        set(recently_installed) -
        set(['wheel'])   # no need to install/uninstall wheel every run
    )

    # Finally, uninstall any extraneous packages
    if extraneous:
        pip(('uninstall', '--yes') + tuple(sorted(extraneous)))

    return 0  # posix:success!


def wait_for_all_subprocesses():
    # TODO: unit-test
    from os import wait
    try:
        while True:
            wait()
    except OSError as error:
        if error.errno == 10:  # no child processes
            return
        else:
            raise


def mark_venv_invalid(venv_path, reqs):
    from os.path import isdir
    if isdir(venv_path):
        print()
        print("Something went wrong! Sending '%s' back in time, so make knows it's invalid." % venv_path)
        print("Waiting for all subprocesses to finish...", end=' ')
        wait_for_all_subprocesses()
        print("DONE")
        run(('touch', venv_path, '--reference', reqs[0], '--date', '1 day ago'))
        print()


def dotpy(filename):
    if filename.endswith('.pyc'):
        return filename[:-1]
    else:
        return filename


def venv_update(stage, venv_path, reqs, venv_args):
    from os.path import join, abspath
    venv_python = abspath(join(venv_path, 'bin', 'python'))
    if stage == 1:
        # we have a random python interpreter active, (possibly) outside the virtualenv we want.
        # make a fresh venv at the right spot, and use it to perform stage 2
        with venv(venv_path, venv_args):
            run((venv_python, dotpy(__file__), '--stage2', venv_path) + reqs + venv_args)
    elif stage == 2:
        import sys
        assert sys.executable == venv_python, "Executable not in venv: %s != %s" % (sys.executable, venv_python)
        # we're activated into the venv we want, and there should be nothing but pip and setuptools installed.
        return do_install(reqs)
    else:
        raise AssertionError('impossible stage value: %r' % stage)


def main():
    from sys import argv
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
