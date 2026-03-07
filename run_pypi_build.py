#! /usr/bin/env python3
"""Thin wrapper calling do_pypi_build in common_build_tools/src."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'common_build_tools' / 'src'))
from do_pypi_build import do_pypi_build_cmd  # pylint: disable=wrong-import-position # noqa: E402


if __name__ == '__main__':
    do_pypi_build_cmd()
