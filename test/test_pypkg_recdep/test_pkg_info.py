#! /usr/local/bin/python3
"""Test package information."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

from copy import deepcopy
import pytest
from packaging.utils import NormalizedName
from packaging.version import Version
from pypkg_recdep.pkg_info import PkgKey


@pytest.mark.parametrize('nam1,ver1,nam2,ver2',
                         [('Abc', '2.3',
                           NormalizedName('abc'), Version('2.3'))])
def test_pkgkey_init_equal(capsys, nam1, ver1, nam2, ver2):
    """Test OK cases of PkgKey init and compare."""
    a = PkgKey(name=deepcopy(nam1), version=deepcopy(ver1))
    b = PkgKey(name=deepcopy(nam2), version=deepcopy(ver2))
    out, err = capsys.readouterr()
    assert a == b
    assert not a < b  # pylint: disable=unnecessary-negation
    assert not a > b  # pylint: disable=unnecessary-negation
    assert not a != b  # pylint: disable=unnecessary-negation
    assert a <= b
    assert not b != a  # pylint: disable=unnecessary-negation
    assert a is not b
    assert a.name == b.name
    assert a.version == b.version
    assert a.name == nam2
    assert a.version == ver2
    assert b.name == nam2
    assert b.version == ver2
    assert hash(a) == hash(b)
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('nam1,ver1,nam2,ver2',
                         [('Abc', '2.3',
                           NormalizedName('abc'), Version('2.3.1'))])
def test_pkgkey_init_not_equal(capsys, nam1, ver1, nam2, ver2):
    """Test OK cases of PkgKey init and compare."""
    a = PkgKey(name=deepcopy(nam1), version=deepcopy(ver1))
    b = PkgKey(name=deepcopy(nam2), version=deepcopy(ver2))
    out, err = capsys.readouterr()
    assert a != b
    assert not a == b  # pylint: disable=unnecessary-negation
    assert a < b
    assert not a > b  # pylint: disable=unnecessary-negation
    assert a != b
    assert a <= b
    assert b != a
    assert a is not b
    assert a.name != b.name or a.version != b.version
    assert hash(a) != hash(b)
    assert '' == out
    assert '' == err
