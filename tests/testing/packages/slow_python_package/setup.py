# pylint:disable=import-error,invalid-name,no-init
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from distutils.command.build import build as _build

from setuptools import setup


class build(_build):

    def run(self):  # I actually don't know why coverage doesn't see this :pragma:nocover:
        # Simulate a slow package
        import time
        time.sleep(5)
        # old style class
        _build.run(self)


setup(
    name=str('slow_python_package'),
    version='0.1.0',
    url='example.com',
    author='nobody',
    author_email='nobody@example.com',
    py_modules=[str('slow_python_package')],
    cmdclass={'build': build},
    options={
        'bdist_wheel': {
            'universal': 1,
        }
    },
)
