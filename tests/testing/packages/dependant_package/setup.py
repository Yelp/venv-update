from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from setuptools import setup


setup(
    name=str('dependant_package'),
    version='1',
    url='example.com',
    author='nobody',
    author_email='nobody@example.com',
    install_requires=[
        'many_versions_package>=2,<4',
        'implicit_dependency',
        'pure_python_package>=0.2.1',
    ],
    options={
        'bdist_wheel': {
            'universal': 1,
        }
    },
)  # pylint:disable=duplicate-code
