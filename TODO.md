
NEXT
====
We plan to work on these as soon as possible.


 - [ ] dogfood venv-update during travis, tox
   - [ ] recommended tox config: install_command=pip-faster --prune {opts} {packages}

* change host-python requirement to simply virtualenv, any version

 - [ ] missing tests
   - [ ] non-default requirements file(s)
   - [ ] run from virtualenv which doesn't have virtualenv installed
   - [ ] update an active virtualenv which wasn't created by venv-update




BACKLOG
=======










ARCHIVE
=======



v1.0: tox support
-----------------

rename project to "pip-faster"
"venv-update" is an auxiliary, vendorable script that depends on the rest of it
pip-faster closely implements the pip interface, with an additional --prune option

* dogfood venv-update during travis, tox

* recommended tox config: install_command=pip-faster --prune {opts} {packages}

* change host-python requirement to simply virtualenv, any version

* missing tests
   * non-default requirements file(s)

* STRETCH GOAL: pip6 support


v2.0: stuff we really want
--------------------------

* pip6 support

* test against select older virtualenv(pip) versions

* speed up the (git|hg)+ case. `pip install` is currently much faster.

* new requirement: move the venv, still be able to us `./bin/thatscript` and `source activate && thatscript`



LATER: Things that I want to do, but would put me past my deadline:
------------------------------------------------------------

* coverage: 105, 124, 135, 184, 242, 281, 285-292, 297-298, 326-328, 461, 465

* populate wheels into the cache *during* build (rather than separate step, beforehand.
    This would shave 5s off all scenarios.
    see: https://github.com/pypa/pip/issues/2140
    see also: https://github.com/pypa/pip/pull/1572

* On ubuntu stock python2.7 I have to rm -rf $VIRTUAL_ENV/local
    to avoid the AssertionError('unexpected third case')
    https://bitbucket.org/ned/coveragepy/issue/340/keyerror-subpy

* I could remove the --cov-config with a small patch to pytest-cov
    use os.path.abspath(options.cov_config) in postprocess(options)

* coverage.py adds some helpful warnings to stderr, with no way to quiet them.
    there's already an issue (#2 i think?), just needs a patch

* pytest-timeout won't actually time-out with floating-point, zero, or negative input

* Make doubly sure these test scenarios are covered:
   * each of these should behave similarly whether caused by the user
     (mucking between venv-updates) or the requirements file:
       * upgrade
       * downgrade
       * add
       * delete

* Go through all my forks/branches and see how close i can get back to master
    some of this stuff has been merged
    wait till March 2014

* pip micro-bug: pip wheel unzips found wheels even with --no-deps

* make a fixture containing the necessary wheels for the enable_coverage function

* pytest-timeout is causing flakiness:
   https://bitbucket.org/flub/pytest-timeout/issue/8/internalerror-valueerror-signal-only-works 

* get README.md working as the long_description on pypi

* try out pbr (?)
    http://docs.openstack.org/developer/pbr/#usage
