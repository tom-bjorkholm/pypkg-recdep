#! /usr/bin/env python3
"""Thin wrapper calling clean_build in common_build_tools/src."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'common_build_tools' / 'src'))
from clean_build import clean_build_cmd  # pylint: disable=wrong-import-position # noqa: E402


if __name__ == '__main__':
    clean_build_cmd()
