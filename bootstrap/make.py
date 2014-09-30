#!/usr/bin/env python
"""Create the bootstrap script."""
# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals

import io
import virtualenv
from os.path import join, dirname


def path(basename):
    return join(dirname(__file__), basename)


def main():
    contents = virtualenv.create_bootstrap_script(
        open(path('content.py')).read()
    )

    with io.open(join(dirname(__file__), 'result.py'), 'w', encoding='UTF-8') as install_file:
        install_file.write(contents)
        # mangle the noqa pragmas slightly to preserve linting for this file
        install_file.write('# flake8:' + 'noqa\n')
        install_file.write('# pylint:' + 'skip-file\n')

acceptance_tests = dict(
    already_built='''
./bootstrap/make.py
git diff   # no output
    ''',
)

if __name__ == '__main__':
    exit(main())
