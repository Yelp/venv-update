#!/usr/bin/env python

from __future__ import unicode_literals
from setuptools import find_packages
from setuptools import setup


def main():
    setup(
        name='venv-update',
        version='0.0a2',
        description="Quickly and exactly synchronize a virtualenv with a requirements.txt",
        url='https://github.com/Yelp/venv-update',
        author='Buck Golemon',
        author_email='buck@yelp.com',
        platforms='all',
        classifiers=[
            'License :: Public Domain',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
        ],
        py_modules=['venv_update'],
        packages=find_packages('.', exclude=('tests*',)),
        install_requires=[
            'virtualenv>=1.11.5',
            'plumbum',  # TODO: remove dep
        ],
        entry_points={
            'console_scripts': [
                'venv-update = venv_update:main',
            ],
        },
    )  # pragma: no cover: covered by tox

if __name__ == '__main__':
    exit(main())
