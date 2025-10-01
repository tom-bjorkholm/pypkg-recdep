#! /usr/local/bin/python3
"""Test exclude information."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

from copy import deepcopy
from tempfile import TemporaryDirectory
import shutil
import pytest
from pypkg_recdep.find_pypi_deps import select_given_lic_file, \
    select_default_lic_file, T, select_lic_file_names, \
    get_lic_text_zip


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
def test_select_giv_lic1(capsys,  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
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


@pytest.mark.parametrize('typ', [AStr, BStr])
@pytest.mark.parametrize('intar,res,msgs,pkgname',
                         [([], [],
                           ['Failed to find license text in package (no named',
                            'Package: abc_d'], 'abc_d'),
                          (['COPYING', 'a/LICENSE.txt'], ['COPYING'],
                           None, 'pkg_a'),
                          (['COPYING', 'LICENSE', 'LICENSE.txt'],
                           ['LICENSE.txt'], None, 'pkg_b'),
                          (['abc', 'd/efg', 'h/LICENSE', 'i/COPYING'],
                           ['h/LICENSE'], None, 'pkg_c')])
def test_select_default_lic1(capsys,  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                             intar, res, msgs, pkgname, typ):
    """Test OK cases of select_default_lic_file."""
    ret = select_default_lic_file(files_in_tar=deepcopy(list(map(typ, intar))),
                                  pkgid=pkgname, _tinfo=typ('a'))
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


@pytest.mark.parametrize('typ', [AStr, BStr])
@pytest.mark.parametrize('ftar,mlic,pkgi,given',
                         [([], [], 'abc', True),
                          (['a', 'c/d'], None, 'efg', False),
                          (['a/b', 'c/d'], ['d'], 'hjk', True)])
def test_select_liv_filnames1(capsys,  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                              monkeypatch, ftar, mlic, pkgi, typ, given):
    """Test selection of function to get license file names."""
    given_called = 0
    def_called = 0

    def sel_giv_lic_file(files_in_tar: list[T], meta_lic_files: list[str],
                         pkgid: str, _tinfo: T) -> list[T]:
        """Mock select given license file."""
        nonlocal given_called
        given_called += 1
        assert files_in_tar == ftar
        assert meta_lic_files == mlic
        assert pkgid == pkgi
        assert _tinfo == typ('a')

    def sel_def_lic_file(files_in_tar: list[T],
                         pkgid: str, _tinfo: T) -> list[T]:
        """Mock select default lic file."""
        nonlocal def_called
        def_called += 1
        assert files_in_tar == ftar
        assert pkgid == pkgi
        assert _tinfo == typ('a')

    mod = 'pypkg_recdep.find_pypi_deps.'
    monkeypatch.setattr(mod + 'select_given_lic_file', sel_giv_lic_file)
    monkeypatch.setattr(mod + 'select_default_lic_file', sel_def_lic_file)
    select_lic_file_names(files_in_tar=deepcopy(list(map(typ, ftar))),
                          meta_lic_files=deepcopy(mlic),
                          pkgid=deepcopy(pkgi),
                          tinfo=deepcopy(typ('a')))
    out, err = capsys.readouterr()
    if given:
        assert given_called == 1
        assert def_called == 0
    else:
        assert given_called == 0
        assert def_called == 1
    assert out == ''
    assert err == ''


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
                            'Package: pkg_d'], 'pkg_d'),
                          (['COPYING', 'a/LICENSE.txt'], None, ['COPYING'],
                           None, 'pkg_a'),])
def test_select_liv_filnames2(capsys,  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                              intar, meta, res, msgs, typ, pkgname):
    """Test OK cases of select_lic_file_names."""
    ret = select_lic_file_names(files_in_tar=deepcopy(list(map(typ, intar))),
                                meta_lic_files=deepcopy(meta),
                                pkgid=deepcopy(pkgname),
                                tinfo=deepcopy(typ('x')))
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


@pytest.mark.parametrize('fname,licfnames,pkgid,restxt,errtxt',
                         [('a.zip', ['a.txt'], 'pkg4',
                           'This text is in a.txt 123\n', ''),
                          ('b.zip', ['a.txt', 'subdir/c.md'], 'pkg5',
                           'This text is in a.txt 123\n' +
                           'This text is in subdir/c.md 567\n', ''),
                          ('c.zip', None, 'pkg6',
                           'This text is in b.md 345\n', ''),
                          ('a.zip', ['all_files.txt'], 'pkg7',
                           '',
                           'Failed to find license text file ' +
                           'all_files.txt in package.\nPackage: pkg7\n')])
def test_get_lic_test_zip(capsys,  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                          fname, licfnames, pkgid, restxt, errtxt):
    """Test OK and error cases of get_lic_text_zip."""
    with TemporaryDirectory() as dirname:
        fullfname = dirname + '/' + deepcopy(fname)
        shutil.copy(src='test/test_pypkg_recdep/pkgtest.zip', dst=fullfname)
        ret = get_lic_text_zip(filename=fullfname,
                               lic_files=deepcopy(licfnames),
                               pkgid=deepcopy(pkgid))
        assert restxt == ret
    out, err = capsys.readouterr()
    assert '' == out
    assert err == errtxt
