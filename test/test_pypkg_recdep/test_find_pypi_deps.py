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


@pytest.mark.parametrize('typ', [AStr, BStr])
@pytest.mark.parametrize('intar,meta,res,msgs,pkgname',
                         [(['a', 'b'], ['a'], ['a'], None, 'my_pkg'),
                          (['x', 'b', 'c', 'd'], ['b', 'd'], ['b', 'd'],
                           None, 'pkg_a'),
                          (['a/c', 'd1', 'd/c', 'e/f'], ['c', 'f'],
                           ['a/c', 'e/f'], None, 'pkg_b'),
                          (['a', 'c'], ['d', 'e'], [],
                           ['Failed to find license text file d in package.',
                            'Failed to find license text file e in package.',
                            'Package: pkg_c'], 'pkg_c'),
                          (['a/c', 'd1', 'd/c', 'e/f'], ['c', 'xx', 'f'],
                           ['a/c', 'e/f'],
                           ['Failed to find license text file xx in package.',
                            'Package: pkg_d'], 'pkg_d')])
def test_select_giv_lic_ok1(capsys,  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                            intar, meta, res, msgs, typ, pkgname):
    """Test OK cases of select_given_lic_file."""
    ret = select_given_lic_file(files_in_tar=deepcopy(list(map(typ, intar))),
                                meta_lic_files=deepcopy(meta),
                                pkgid=pkgname, _tinfo=typ('x'))
    out, err = capsys.readouterr()
    assert res == ret
    if ret:
        assert isinstance(ret[0], typ)
    assert '' == out
    if msgs:
        for m in msgs:
            assert m in err
    else:
        assert '' == err
