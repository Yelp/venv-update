#!/usr/bin/env python

from __future__ import unicode_literals
from setuptools import find_packages
from setuptools import setup


def main():
    setup(
        name='venv-update',
        version='0.1.2dev0',
        description="Quickly and exactly synchronize a virtualenv with a requirements.txt",
        url='https://github.com/Yelp/venv-update',
        author='Buck Golemon',
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
        py_modules=['venv_update'],
        packages=find_packages('.', exclude=('tests*',)),
        install_requires=[
            'virtualenv>=1.11.5,<2.0',
        ],
        entry_points={
            'console_scripts': [
                'venv-update = venv_update:main',
            ],
        },
        keywords=['pip', 'virtualenv'],
    )  # pragma: no cover: covered by tox

if __name__ == '__main__':
    exit(main())
