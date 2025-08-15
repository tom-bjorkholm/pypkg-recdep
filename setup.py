#! /usr/local/bin/python3
"""Setup file specifying build of .whl."""

from setuptools import setup

setup(
  name='pypkg-recdep',
  version='0.1',
  description='Recursively find dependencies for PyPI packages',
  author='Tom Björkholm',
  author_email='klausuler_linnet0q@icloud.com',
  python_requires='>=3.12',
  packages=['pypkg_recdep'],
  package_dir={'pypkg_recdep': 'src/pypkg_recdep'},
  package_data={'ppypkg_recdep': ['src/py.typed']},
  install_requires=[
    'pypi-simple >= 1.7.0',
    'packaging >= 25.0',
    'argcomplete >= 3.6.2',
    'requests >= 2.32.4',
    'types-requests >= 2.32.4.20250809',
    'pip >= 25.2',
    'setuptools >= 80.9.0',
    'build >= 1.3.0',
    'wheel>=0.45.1'
  ]
)
