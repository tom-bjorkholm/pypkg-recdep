#! /bin/zsh
#
# Copyright (c) 2024-2025 Tom Björkholm
# MIT License
#
if [ ! -z "${VIRTUAL_ENV}" ] ; then
  echo "Cannot delete virtual environment if already in virtual environment"
  echo "First do: deactivate "
  exit 1
fi
rm -rf build dist reports venv .pytest_cache .mypy_cache
rm -rf .coverage*
find . -name __pycache__ -exec rm -rf {} \;
find . -name '*~' -exec rm {} \;
find . -name '*.egg-info' -exec rm -rf {} \;
find . -name '*.pyc' -exec rm {} \;
find . -name '.coverage' -exec rm {} \;
find . -name '.tox' -exec rm {} \;
find . -name 'nosetests.xml' -exec rm {} \;
