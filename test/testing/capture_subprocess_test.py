import pytest

from .capture_subprocess import make_outputter, capture_subprocess


# buglet: floating-point, zero, negative values interpreted as infinite =/
@pytest.mark.timeout(1)  # should take <.5s
def test_capture_subprocess(tmpdir):
    tmpdir.chdir()
    make_outputter()

    cmd = ('python', 'outputter.py')
    stdout, stderr, combined = capture_subprocess(cmd)

    assert stdout.count('\n') == 3207
    assert stderr.count('\n') == 793
    assert combined.count('\n') == 4000

    assert stdout.strip('.\r\n') == ''
    assert stderr.strip('%\r\n') == ''

    # I'd like to assert that the two streams are interleaved strictly by line,
    # but I haven't been able to produce such output reliably =/

    assert len(stdout) + len(stderr) == len(combined)
