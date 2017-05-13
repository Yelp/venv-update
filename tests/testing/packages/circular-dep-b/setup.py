from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from setuptools import setup


setup(
    name=str('circular-dep-b'),
    version='1.0',
    url='example.com',
    author='nobody',
    author_email='nobody@example.com',
    install_requires=[
        'circular-dep-a==1.0',
    ],
    options={
        'bdist_wheel': {
            'universal': 1,
        }
    },
)
