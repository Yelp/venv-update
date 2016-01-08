from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import pip_faster as P


def test_patch():
    d = {1: 1, 2: 2}
    patches = {2: 3}.items()
    orig = P.patch(d, patches)

    assert d == {1: 1, 2: 3}
    assert orig == {2: 2}

    try:
        P.patch(d, {3: 3}.items())
        raise AssertionError('expected KeyError')
    except KeyError:
        pass


def test_patched():
    d = {1: 1, 2: 2}
    patches = {2: 3}

    before = d.copy()
    with P.patched(d, patches) as orig:
        assert d == {1: 1, 2: 3}
        assert orig == {2: 2}

    assert d == before

    try:
        with P.patched(d, {3: 3}):
            raise AssertionError('expected KeyError')
    except KeyError:
        pass
