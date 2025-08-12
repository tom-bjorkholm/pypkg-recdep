#! /usr/local/bin/python3
"""Test package information."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

from copy import deepcopy
import pytest
from packaging.utils import NormalizedName
from packaging.version import Version
from pypkg_recdep.pkg_info import PkgKey, create_pkginfo, PkgInfo, Pkgs


@pytest.mark.parametrize('nam1,ver1,nam2,ver2,tnam, tver',
                         [('Abc', '2.3',
                           NormalizedName('abc'), Version('2.3'),
                           NormalizedName('abc'), Version('2.3')),
                          (NormalizedName('def'), '4.5',
                           'DeF', Version('4.5'),
                           NormalizedName('def'), Version('4.5')),
                          ('GHI', Version('6.7'),
                           NormalizedName('ghi'), '6.7',
                           NormalizedName('ghi'), Version('6.7')),
                          (NormalizedName('jkl'), Version('8.9'),
                           'jKL', '8.9',
                           NormalizedName('jkl'), Version('8.9'))])
def test_pkgkey_init_equal(capsys,  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                           nam1, ver1, nam2, ver2, tnam, tver):
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
    assert hash(a) == hash(b)
    assert a.name == tnam
    assert a.version == tver
    assert b.name == tnam
    assert b.version == tver
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('nam1,ver1,nam2,ver2',
                         [('Abc', '2.3',
                           NormalizedName('abc'), Version('2.3.1')),
                          ('Abc', '2.3',
                           NormalizedName('abcd'), Version('2.3')),
                          (NormalizedName('xyz'), Version('7.8'),
                           'yz', '7.8'),
                          (NormalizedName('xyz'), Version('7.8'),
                           'xyz', '7.9')])
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


@pytest.mark.parametrize('nam,ver',
                         [('abc', '2.3'), ('gh', '9.1.3')])
def test_create_pkg_info(capsys, nam, ver):
    """Test OK cases of create_pkg_info."""
    a = PkgKey(name=deepcopy(nam), version=deepcopy(ver))
    c = PkgInfo(key=deepcopy(a), metadata_version=None, license=None,
                project_urls={}, homepage=None, source_url=None,
                maintainer=None, dependencies=[], license_text=None)
    b = create_pkginfo(key=a)
    assert c == b
    out, err = capsys.readouterr()
    assert str(b['key'].name) == nam
    assert b['key'].version == Version(ver)
    assert '' == out
    assert '' == err


def test_pkgs_dict(capsys):
    """Test using dict Pkgs."""
    data = [
        ('hg', '3.1', 'abc'),
        ('ag', '5.1', 'def'),
        ('au', '10.1.4', 'ghi'),
        ('au', '11.2', 'jkl'),
        ('ag', '5.1', 'mno'),
        ('au', '11.2', 'pqr')
    ]
    pkgs: Pkgs = {}
    for i in data:
        key = PkgKey(name=deepcopy(i[0]), version=deepcopy(i[1]))
        pkgs[key] = create_pkginfo(key=key)
        pkgs[key]['license_text'] = deepcopy(i[2])
    assert len(pkgs) == 4
    assert pkgs[PkgKey(name='hg', version='3.1')]['license_text'] == 'abc'
    assert pkgs[PkgKey(name='ag', version='5.1')]['license_text'] == 'mno'
    assert pkgs[PkgKey(name='au', version='10.1.4')]['license_text'] == 'ghi'
    assert pkgs[PkgKey(name='au', version='11.2')]['license_text'] == 'pqr'
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


def test_pkg_key_str(capsys):
    """Simple test of PkgKey.__str__."""
    key = PkgKey(name='xyz', version='1.3.2')
    assert "{'name': 'xyz', 'version': <Version('1.3.2')>}" == str(key)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
