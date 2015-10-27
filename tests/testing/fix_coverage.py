#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os

from coverage.data import CoverageData


def merge_coverage(coverage_data, from_path, to_path):
    for filename in tuple(coverage_data.lines):
        result_filename = filename.split(from_path)[-1]
        if filename == result_filename:
            continue

        result_filename = os.path.join(to_path, result_filename)
        if not os.path.exists(result_filename):
            continue

        coverage_data.lines.setdefault(result_filename, {})
        coverage_data.lines[result_filename].update(coverage_data.lines[filename])
        coverage_data.arcs.setdefault(result_filename, {})
        coverage_data.arcs[result_filename].update(coverage_data.arcs[filename])

        del coverage_data.lines[filename]
        del coverage_data.arcs[filename]


def fix_coverage(from_path, to_path):
    coverage_data = CoverageData()
    os.rename('.coverage', '.coverage.orig')
    coverage_data.read_file('.coverage.orig')
    merge_coverage(coverage_data, from_path, to_path)
    coverage_data.write_file('.coverage')


def main():
    from sys import argv
    from_path, to_path = argv[1:]
    fix_coverage(from_path, to_path)


if __name__ == '__main__':
    exit(main())
