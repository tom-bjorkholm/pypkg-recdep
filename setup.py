#! /usr/local/bin/python3
"""Setup file specifying build of .whl."""

from setuptools import setup

setup(
  name='pypkg-recdep',
  version='0.7.1',
  description='Recursively find dependencies for PyPI packages',
  author='Tom Björkholm',
  author_email='klausuler_linnet0q@icloud.com',
  python_requires='>=3.12',
  packages=['pypkg_recdep'],
  package_dir={'pypkg_recdep': 'src/pypkg_recdep'},
  package_data={'ppypkg_recdep': ['src/py.typed']},
  install_requires=[
    'mformat >= 0.7',
    'pypi-simple >= 1.8.0',
    'packaging >= 26.2',
    'argcomplete >= 3.7.0',
    'requests >= 2.34.2',
    'types-requests >= 2.33.0.20260518'
  ]
)
