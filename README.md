# venv-update
[![Build Status](https://travis-ci.org/Yelp/venv-update.svg?branch=master)](https://travis-ci.org/Yelp/venv-update)
[![Coverage Status](https://img.shields.io/coveralls/Yelp/venv-update.svg?branch=master)](https://coveralls.io/r/Yelp/venv-update)

`venv-update` is a tool for keeping a virtualenv up-to-date with version-controlled requirement lists.
It's optimized for big projects (hundreds of requirements), and as such makes heavy use of caches, wheels and wheel-caches. We use it when working on the main Yelp codebase. The tool also ensures that no "extraneous" packages are installed after an update; the goal is that your virtualenv in the same state as if you had rebuilt it from scratch, but *much* more quickly.


## Installation

Because this tool is meant to be the entry-point for handling requirements and dependencies, it's not meant to be installed via pip usually. The design allows the single venv_update.py to be vendored (directly checked in) to your project, and run without any dependencies beyond the python standard library.


## Usage


Simply running `venv_update.py` will create a virtualenv named `virtualenv_run` in the current directory, using `requirements.txt` in the current directory. These are default values that can be overridden by providing arguments. Pass `--help` for more detail.


## Features:

 * Caching: All downloads and wheels are cached (in `~/.pip/cache` and `~/.pip/wheelhouse`, respectively). You shouldn't have to wait for anything to download or build twice.
 * All packages are built to wheels before installation. This means that if you're using a package that takes a bit to compile (`lxml`) or on a platform that doesn't have public-pypi wheel support (linux), you still get the speed advantages associated with wheels.
 * Extraneous packages are uninstalled. This helps ensure that your dev environment isn't polluted by any previous state of your project. "Extraneous" packages are those that are neither directly required, nor required by any direct requirement.
 * Dependency conflict detection: stock pip will happily install two packages with conflicting requirements, with undefined behavior for the conflicted requirement. For now, venv-update gives the same result as pip, but at least throws you a yellow warning when such a situation arises. In future (once we fix our code base's issues) this will be an error.
 * Minimize pypi round-trips: We've taken great pains to reduce the number of round-trips to pypi, which makes up the majority of time spent on what should be a no-op update. With a properly warmed cache, you should be able to rebuild your virtualenv with no network access.
