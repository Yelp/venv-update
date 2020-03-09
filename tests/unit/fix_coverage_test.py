from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from coverage.data import CoverageData

from testing.fix_coverage import merge_coverage


def test_fix_coverage(tmpdir):
    base_file = tmpdir.join('foo.py')
    base_file.ensure()
    sub_file = tmpdir.join('site-packages/foo.py')
    sub_file.ensure()
    unrelated_file = tmpdir.join('bar.py')
    unrelated_file.ensure()

    coverage_data = CoverageData(basename='.coverage.orig')
    coverage_data.add_arcs({
        str(base_file): {(1, 2): None},
        str(sub_file): {(3, 4): None},
        str(unrelated_file): {(5, 6): None},
    })

    assert coverage_data.lines(base_file) == [1, 2]
    assert coverage_data.lines(sub_file) == [3, 4]
    assert coverage_data.lines(unrelated_file) == [5, 6]

    new_coverage_data = merge_coverage(coverage_data, '/site-packages/', str(tmpdir))

    # The new file should contain all the lines and arcs
    assert new_coverage_data.lines(base_file) == [1, 2, 3, 4]
    assert new_coverage_data.arcs(base_file) == [(1, 2), (3, 4)]
    assert new_coverage_data.lines(unrelated_file) == [5, 6]
    assert new_coverage_data.arcs(unrelated_file) == [(5, 6)]

    # And it should not contain the original, un-merged names.
    assert sub_file not in new_coverage_data.measured_files()
