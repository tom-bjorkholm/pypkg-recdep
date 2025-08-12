#! /usr/local/bin/python3
"""Test exclude information."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

from copy import deepcopy
# from tempfile import TemporaryDirectory
import pytest
from pypkg_recdep.find_pypi_deps import select_given_lic_file


class AStr(str):
    """Type AStr based on str for testing."""


class BStr(str):
    """Type Bstr based on str for testing."""


@pytest.mark.parametrize('intar,meta,res',
                         [([AStr('a'), AStr('b')], ['a'], [AStr('a')])])
def test_select_giv_lic_ok1(capsys, intar, meta, res):
    """Test OK cases of select_given_lic_file."""
    ret = select_given_lic_file(files_in_tar=deepcopy(intar),
                                meta_lic_files=deepcopy(meta),
                                pkgid='my_pkg', _tinfo=AStr('x'))
    out, err = capsys.readouterr()
    assert res == ret
    assert '' == out
    assert '' == err
