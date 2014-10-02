#!/usr/bin/env python

from setuptools import find_packages
from setuptools import setup


def main():
    setup(
        name='venv-update',
        version='0.0',
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
        packages=find_packages('.', exclude=('tests*',)),
        install_requires=[
            'plumbum',
            'virtualenv',
        ],
        entry_points={
            'console_scripts': [
                'venv-update = venv_update.cli:main',
            ],
        },
    )  # pragma: no cover: covered by tox

if __name__ == '__main__':
    exit(main())
