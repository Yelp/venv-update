from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from setuptools import setup


setup(
    name=str('pure_python_package'),
    version='0.2.1',
    url='example.com',
    author='nobody',
    author_email='nobody@example.com',
    py_modules=[str('pure_python_package')],
    extras_require={
        'my-extra': ['implicit_dependency'],
    },
    entry_points={
        'console_scripts': [
            'pure-python-script = pure_python_package:main',
        ],
    },
    options={
        'bdist_wheel': {
            'universal': 1,
        }
    },
)  # pylint:disable=duplicate-code
