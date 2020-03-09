#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os.path

import coverage.env
from coverage.data import CoverageData
coverage.env.TESTING = 'true'


def merge_coverage(coverage_data, from_path, to_path):
    new_coverage_data = CoverageData()
    assert coverage_data._filename != new_coverage_data._filename

    for filename in coverage_data.measured_files():
        result_filename = filename.split(from_path)[-1]
        if filename != result_filename:
            result_filename = result_filename.lstrip('/')
            result_filename = os.path.join(to_path, result_filename)
            result_filename = os.path.abspath(result_filename)
            assert os.path.exists(result_filename), result_filename

        new_coverage_data.add_arcs(
            {result_filename: coverage_data.arcs(filename)}
        )

    return new_coverage_data


def fix_coverage(from_path, to_path):
    os.rename('.coverage', '.coverage.orig')
    coverage_data = CoverageData(basename='.coverage.orig')
    coverage_data.read()
    new_coverage_data = merge_coverage(coverage_data, from_path, to_path)
    new_coverage_data.write()


def main():
    from sys import argv
    from_path, to_path = argv[1:]
    fix_coverage(from_path, to_path)


if __name__ == '__main__':
    exit(main())
