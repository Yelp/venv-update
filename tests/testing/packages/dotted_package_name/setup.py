from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from setuptools import setup


setup(
    name=str('dotted.package-name'),
    version='0.1.0',
    url='example.com',
    author='nobody',
    author_email='nobody@example.com',
    py_modules=[str('dotted_package_name')],
    options={
        'bdist_wheel': {
            'universal': 1,
        }
    },
)
