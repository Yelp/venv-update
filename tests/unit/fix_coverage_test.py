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

    coverage_data = CoverageData()
    coverage_data.add_line_data({
        str(base_file): {0: None, 1: None},
        str(sub_file): {2: None, 3: None},
        str(unrelated_file): {4: None, 5: None},
    })
    coverage_data.add_arc_data({
        str(base_file): {(0, 1): None},
        str(sub_file): {(2, 3): None},
        str(unrelated_file): {(4, 5): None},
    })

    merge_coverage(coverage_data, '/site-packages/', str(tmpdir))

    # The base file should contain all the lines and arcs
    assert coverage_data.line_data()[base_file] == [0, 1, 2, 3]
    assert coverage_data.arc_data()[base_file] == [(0, 1), (2, 3)]

    # And the sub file should no longer exist
    assert sub_file not in coverage_data.lines
    assert sub_file not in coverage_data.arcs
