# venv-update
[![Build Status](https://travis-ci.org/Yelp/venv-update.svg?branch=master)](https://travis-ci.org/Yelp/venv-update)
[![Coverage Status](https://img.shields.io/coveralls/Yelp/venv-update.svg?branch=master)](https://coveralls.io/r/Yelp/venv-update)

Venv-update is a tool for keeping a virtualenv up-to-date with version-controlled requirement lists.
It's optimized for big projects (hundreds of requirements), and a such makes heavy use of caches and wheels, and wheel-caches. We use it when working on the main Yelp codebase. The tool also ensures that no "extraneous" packages are installed after an update; the goal is that your virtualenv in the same state as if you had rebuilt it from scratch, but *much* more quickly.


## Installation

Because this tool is meant to be the entry-point for handling requirements and dependencies, it's not meant to be installed via pip usually. The design allows the single venv_update.py to be vendored into your project without any dependencies.


## Usage


Simply running `venv_update.py` will create a virtualenv named `virtualenv_run` in the current directory, using `requirements.txt` in the current directory. These are default values that can be overridden by providing arguments. Pass `--help` for more detail.
