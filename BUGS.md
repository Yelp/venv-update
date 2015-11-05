This is a simple listing of bugs previously encountered:

Known Bugs
============

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


Fixed and Tested
================

(none, yet)
