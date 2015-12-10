from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from setuptools import setup


class broken_bdist_wheel(object):
    """This isn't even a valid command class."""


setup(
    name=str('cant_wheel_package'),
    version='0.1.0',
    url='example.com',
    author='nobody',
    author_email='nobody@example.com',
    cmdclass={'bdist_wheel': broken_bdist_wheel},
)  # pylint:disable=duplicate-code
