#!/bin/zsh
#
# Copyright (c) 2024-2025 Tom Björkholm
# MIT License
#
if [ ${#} -gt 0 ]; then
    PYTHON=${1}
    if echo ${PYTHON} | grep -v 'python' > /dev/null
    then
        echo ${PYTHON} 'does not look like a python version'
        exit 1
    fi
    if which ${PYTHON} > /dev/null
    then
        echo 'Using PYTHON' ${PYTHON} 
    else
        echo 'Cannot find executable for' ${PYTHON}
        exit 1
    fi
fi
if [[ ! -v PYTHON ]]; then
    PYTHON=`./bestInstalledPython.zsh`
fi
echo 'Using PYTHON' ${PYTHON} 
set -eE
trap 'printf "\e[31m%s: %s\e[m\n" "Exiting due to error code from command" $?' ERR
set -v
if [ ! -z "${VIRTUAL_ENV}" ] ; then
  echo "Cannot set up build environment if already in virtual environment"
  exit 1
fi
if [ -d venv ] ; then
  echo "Virtual environment already present. "
  echo "To delete virtual environment and reinitialize type any character and press <enter>"
  echo "To abort press ctrl-C"
  read a
  rm -rf venv
fi
${PYTHON} -m pip install --upgrade pip
${PYTHON} -m pip install --upgrade setuptools
${PYTHON} -m pip install --upgrade build
${PYTHON} -m pip install twine==6.0.1
${PYTHON} -m venv venv
. ./venv/bin/activate
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
