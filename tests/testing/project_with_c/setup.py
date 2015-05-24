from setuptools import Extension
from setuptools import setup


setup(
    name='project_with_c',
    version='0.1.0',
    ext_modules=[Extension('project_with_c', ['project_with_c.c'])],
)
