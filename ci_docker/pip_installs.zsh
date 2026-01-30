#! /bin/zsh

# Copyright (c) 2025 Tom Björkholm
# MIT License
#

for PYTHON in python3.10 python3.11 python3.12 python3.13 python3.14
do
    for pkg in pip pylint lxml mypy coverage build setuptools \
               pytest pytest-html flake8 flake8-html pytest-flake8 \
               pytest-skip-slow flake8-docstrings pytest-pylint \
               pytest-cov wheel pypi-simple requests types-requests \
               argcomplete xmltodict types-xmltodict Pillow packaging \
               openpyxl types-openpyxl pylightxl XlsxWriter \
               extract-list excel-list-transform python-docx \
               odfpy msl-odt python-docx mformat
    do
        ${PYTHON} -m pip install --upgrade ${pkg}
    done
    ${PYTHON} -m pip install twine==6.0.1
done
