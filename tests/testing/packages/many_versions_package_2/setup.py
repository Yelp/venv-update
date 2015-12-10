from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from setuptools import setup


setup(
    name=str('many_versions_package'),
    version='2',
    url='example.com',
    author='nobody',
    author_email='nobody@example.com',
    options={
        'bdist_wheel': {
            'universal': 1,
        }
    },
)  # pylint:disable=duplicate-code
