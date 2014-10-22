import pytest

from .capture_subprocess import capture_subprocess


def make_outputter():
    """Create the the outputter.py script, for the demonstration."""
    with open('outputter.py', 'w') as outputter:
        outputter.write('''\
from __future__ import print_function
from __future__ import division
from sys import stdout, stderr
from time import sleep
from random import random, seed
seed(0)  # unpredictable, but repeatable

# system should not deadlock for any given value of these parameters.
LINES = 10
TIME = 0
WIDTH = 79
ERROR_RATIO = .20

for i in range(LINES):
    if random() > ERROR_RATIO:
        char = '.'
        file = stdout
    else:
        char = '%'
        file = stderr

    for j in range(WIDTH):
        print(char, file=file, end='')
        sleep(TIME / LINES / WIDTH)
    print(file=file)
''')


# buglet: floating-point, zero, negative values interpreted as infinite =/
@pytest.mark.timeout(1)  # should take <.5s
def test_capture_subprocess(tmpdir):
    tmpdir.chdir()
    make_outputter()

    cmd = ('python', 'outputter.py')
    stdout, stderr, combined = capture_subprocess(cmd)

    #assert stdout.count('\n') == 10
    #assert stderr.count('\n') == 0
    #assert combined.count('\n') == 14

    #assert stdout.strip('.\r\n') == ''
    #assert stderr.strip('%\r\n') == ''

    # I'd like to assert that the two streams are interleaved strictly by line,
    # but I haven't been able to produce such output reliably =/

    assert len(stdout) + len(stderr) == len(combined)
