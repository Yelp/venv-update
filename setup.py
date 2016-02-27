#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from setuptools import find_packages
from setuptools import setup


# https://github.com/pypa/python-packaging-user-guide/blob/master/source/single_source_version.rst
def read(*names, **kwargs):
    import io
    import os
    with io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ) as fp:
        return fp.read()


def find_version(*file_paths):
    import re
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


def main():
    setup(
        name='venv-update',
        version=find_version('venv_update.py'),
        description="quickly and exactly synchronize a large project's virtualenv with its requirements",
        url='https://github.com/Yelp/venv-update',
        author='Buck Evan',
        author_email='buck@yelp.com',
        platforms='all',
        license='MIT',
        classifiers=[
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: Implementation :: PyPy',
            'Topic :: System :: Archiving :: Packaging',
            'Operating System :: Unix',
            'Intended Audience :: Developers',
            'Development Status :: 4 - Beta',
            'Environment :: Console',
        ],
        py_modules=['venv_update', 'pip_faster'],
        packages=find_packages('.', exclude=('tests*',)),
        install_requires=[
            'pip>=1.5.0,<6.0.0',
            'wheel>0.25.0',  # 0.25.0 causes get_tag AssertionError in python3
            'setuptools>=0.8.0',  # 0.7 causes "'sys_platform' not defined" when installing wheel >0.25
        ],
        entry_points={
            'console_scripts': [
                'venv-update = venv_update:main',
                'pip-faster = pip_faster:main',
            ],
        },
        keywords=['pip', 'virtualenv'],
        options={
            'bdist_wheel': {
                'universal': 1,
            }
        },
    )  # :pragma:nocover: covered by tox

if __name__ == '__main__':
    exit(main())
