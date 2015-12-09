from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from setuptools import Extension
from setuptools import setup


setup(
    name=str('project_with_c'),
    version='0.1.0',
    ext_modules=[Extension(str('project_with_c'), [str('project_with_c.c')])],
    entry_points={
        'console_scripts': [
            'c-extension-script = project_with_c:hello_world',
        ],
    },
)  # pylint:disable=duplicate-code
