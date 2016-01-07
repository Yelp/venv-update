This is a simple listing of bugs previously encountered:

Known Bugs
============
This is just a place to brain-dump bugs I've found so I don't go insane trying to remember them.
It's much lighter weight than filing tickets, and I like that it's version controlled.

    * venv-update shows the same `> virtualenv venv` line twice in a row

    * the first venv-update fails with "filename too long" in a download cache file,
        but subsequent run succeeds
        TESTCASE: add a super-extra-really-obscenely-long-named-package
        FIX: don't set download-cache within pip-faster. i dont think it was speeding anything up. the wheels are what
        matter.

    * if the "outer" pip is >6, installing pip1.5 shows "a valid SSLContext is not available" and "a newer pip is available"
        we can suppress these with PIP_NO_PIP_VERSION_CHECK and python -W 'ignore'

    * venv-update can `rm -rf .`, if '.' is its first argument.

    * Explosion when argparse is not installed:

       $ pip-faster install argparse
       Traceback (most recent call last):
         File "/nail/home/buck/trees/yelp/pip-faster/venv/bin/pip-faster", line 5, in <module>
           from pkg_resources import load_entry_point
         File "/nail/home/buck/trees/yelp/pip-faster/venv/lib/python2.6/site-packages/pkg_resources.py", line 2749, in <module>
           working_set = WorkingSet._build_master()
         File "/nail/home/buck/trees/yelp/pip-faster/venv/lib/python2.6/site-packages/pkg_resources.py", line 444, in _build_master
           ws.require(__requires__)
         File "/nail/home/buck/trees/yelp/pip-faster/venv/lib/python2.6/site-packages/pkg_resources.py", line 725, in require
           needed = self.resolve(parse_requirements(requirements))
         File "/nail/home/buck/trees/yelp/pip-faster/venv/lib/python2.6/site-packages/pkg_resources.py", line 628, in resolve
           raise DistributionNotFound(req)
       pkg_resources.DistributionNotFound: argparse


Annoyances
==========

    * `capture_subprocess` doesn't properly proxy tty input/output.
      see: https://github.com/bukzor/ptyproxy


Fixed, Not Tested
=================

pip-faster install:

    * Explosion on "Requirement already satisfied" -- `'InstallRequirement' object has no attribute 'best_installed'`
      Fix: factor out the best_installed attribute entirely -- yay

    * install incurs build time twice
      Fix: nasty hack to remove non-wheel source and replace with unzipped wheel

    * wheel-install can install a prior version
      Fix: terribad code to use the wheel with maximum pkg_resources.parse_version

    * Cause: a prior prune uninstalled argparse, but pip-faster depends on it, transitively, via wheel
      Planned fix: for the purposes of pruning, pip-faster should be added to the list of requirements
      Stopgap fix: whitelist argparse along with pip-faster, pip, setuptools, and wheel to never be pruned

test:
    * during make-sdists, the setup.py for pip-faster went missing, once
      Cause: parallel test fixtures were stomping on each others' egg-info
      Fix: set a --egg-dir for egg-info


Magically Fixed
===============

    * `print 1; print 2` is coming from somewhere during py.test -s

Fixed and Tested
================

(none, yet)
