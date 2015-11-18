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
        name='pip-faster',
        version=find_version('venv_update.py'),
        description='Quickly and exactly synchronize a virtualenv with a requirements.txt',
        url='https://github.com/Yelp/pip-faster',
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
            'virtualenv>=1.11.5,<2.0',  # just for venv-update
            'pip>=1.5.0,<6.0.0',
            'wheel',
        ],
        entry_points={
            'console_scripts': [
                'venv-update = venv_update:main',
                'pip-faster = pip_faster:main',
            ],
        },
        keywords=['pip', 'virtualenv'],
    )  # pragma: no cover: covered by tox

if __name__ == '__main__':
    exit(main())
