#! /usr/bin/env python3
"""Thin wrapper calling setup_build_environment in common_build_tools/src."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'common_build_tools' / 'src'))
from setup_build_environment import setup_build_environment_cmd  # pylint: disable=wrong-import-position # noqa: E402


if __name__ == '__main__':
    setup_build_environment_cmd()
