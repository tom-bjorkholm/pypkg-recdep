#! /bin/zsh

# Copyright (c) 2025 Tom Björkholm
# MIT License
#

for PYTHON in python3.10 python3.11 python3.12 python3.13 python3.14
do
    ${PYTHON} -m pip install --upgrade pip
    ${PYTHON} -m pip install --upgrade pylint
    ${PYTHON} -m pip install --upgrade lxml
    ${PYTHON} -m pip install --upgrade mypy
    ${PYTHON} -m pip install --upgrade coverage
    ${PYTHON} -m pip install --upgrade build
    ${PYTHON} -m pip install --upgrade setuptools
    ${PYTHON} -m pip install twine==6.0.1
    ${PYTHON} -m pip install --upgrade pytest
    ${PYTHON} -m pip install --upgrade pytest-html
    ${PYTHON} -m pip install --upgrade flake8
    ${PYTHON} -m pip install --upgrade flake8-html
    ${PYTHON} -m pip install --upgrade pytest-flake8
    ${PYTHON} -m pip install --upgrade pytest-skip-slow
    ${PYTHON} -m pip install --upgrade flake8-docstrings
    ${PYTHON} -m pip install --upgrade pytest-pylint
    ${PYTHON} -m pip install --upgrade pytest-cov
    ${PYTHON} -m pip install --upgrade wheel
    ${PYTHON} -m pip install --upgrade pypi-simple
    ${PYTHON} -m pip install --upgrade requests
    ${PYTHON} -m pip install --upgrade types-requests
    ${PYTHON} -m pip install --upgrade argcomplete
done
