#! /usr/bin/env python3
"""Thin wrapper calling clean in common_build_tools/src."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'common_build_tools' / 'src'))
from clean import clean_cmd  # pylint: disable=wrong-import-position # noqa: E402


if __name__ == '__main__':
    clean_cmd()
