#! /usr/local/bin/python3
"""Test exclude information."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

from copy import deepcopy
from tempfile import TemporaryDirectory
import shutil
import pickle
from tarfile import TarInfo
import pytest
from requests import HTTPError
from pypi_simple import NoDigestsError
from packaging.version import Version
from pypkg_recdep.find_pypi_deps import select_given_lic_file, \
    select_default_lic_file, T, select_lic_file_names, \
    get_lic_text_zip, get_lic_text_tar, _fname_to_str, \
    get_license_text, get_environment, get_requirements


class AStr(str):
    """Type AStr based on str for testing."""


class BStr(str):
    """Type Bstr based on str for testing."""


@pytest.mark.parametrize('typ', [AStr, BStr, TarInfo])
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
    ret = select_given_lic_file(files_in_tar=list(map(typ, deepcopy(intar))),
                                meta_lic_files=deepcopy(meta),
                                pkgid=pkgname, _tinfo=typ('x'))
    assert len(res) == len(ret)
    retval: list[str] = []
    for retelem in ret:
        retval.append(_fname_to_str(retelem))
    assert retval == res
    out, err = capsys.readouterr()
    if ret:
        assert isinstance(ret[0], typ)
    assert '' == out
    if msgs:
        for m in msgs:
            assert m in err
    else:
        assert '' == err


@pytest.mark.parametrize('typ', [AStr, BStr, TarInfo])
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
    assert len(res) == len(ret)
    retval: list[str] = []
    for retelem in ret:
        retval.append(_fname_to_str(retelem))
    assert retval == res
    out, err = capsys.readouterr()
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
    if given:
        assert given_called == 1
        assert def_called == 0
    else:
        assert given_called == 0
        assert def_called == 1
    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


@pytest.mark.parametrize('typ', [AStr, BStr])
@pytest.mark.parametrize('intar,meta,res,msgs,pkgname',
                         [(['a', 'b'], ['a'], ['a'], None, 'my_pkg'),
                          (['./a', './b'], ['a'], ['./a'], None, 'my_pkg'),
                          (['x', 'b', 'c', 'd'], ['b', 'd'], ['b', 'd'],
                           None, 'pkg_a'),
                          (['a/c', 'd1', 'd/c', 'e/f'], ['c', 'f'],
                           ['a/c', 'e/f'], None, 'pkg_b'),
                          (['./a/c', './d1', './d/c', './e/f'], ['c', 'f'],
                           ['./a/c', './e/f'], None, 'pkg_b'),
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
def test_select_lic_filnames2(capsys,  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                              intar, meta, res, msgs, typ, pkgname):
    """Test OK cases of select_lic_file_names."""
    ret = select_lic_file_names(files_in_tar=deepcopy(list(map(typ, intar))),
                                meta_lic_files=deepcopy(meta),
                                pkgid=deepcopy(pkgname),
                                tinfo=deepcopy(typ('x')))
    assert res == ret
    if ret:
        assert isinstance(ret[0], typ)
    out, err = capsys.readouterr()
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


@pytest.mark.parametrize('fname,licfnames,pkgid,restxt,errtxt',
                         [('a.tar.gz', ['a.txt'], 'pkg4',
                           'This text is in a.txt 123\n', ''),
                          ('b.tgz', ['a.txt', 'subdir/c.md'], 'pkg5',
                           'This text is in a.txt 123\n' +
                           'This text is in subdir/c.md 567\n', ''),
                          ('c.tar.gz', None, 'pkg6',
                           'This text is in b.md 345\n', ''),
                          ('a.tar.gz', ['all_files.txt'], 'pkg7',
                           '',
                           'Failed to find license text file ' +
                           'all_files.txt in package.\nPackage: pkg7\n')])
def test_get_lic_test_tar(capsys,  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                          fname, licfnames, pkgid, restxt, errtxt):
    """Test OK and error cases of get_lic_text_zip."""
    with TemporaryDirectory() as dirname:
        fullfname = dirname + '/' + deepcopy(fname)
        shutil.copy(src='test/test_pypkg_recdep/pkgtest2.tar.gz',
                    dst=fullfname)
        ret = get_lic_text_tar(filename=fullfname,
                               lic_files=deepcopy(licfnames),
                               pkgid=deepcopy(pkgid))
        assert restxt == ret
    out, err = capsys.readouterr()
    assert '' == out
    assert err == errtxt


class MockClient():  # pylint: disable=too-few-public-methods
    """Mock PyPISImple client."""

    def __init__(self, file, exception):
        """Create a Mocked PYPISimple client object."""
        self.file = file
        self.exception = exception

    def download_package(self, pkg, path, timeout):
        """Get a file as if was downloaded."""
        if self.exception is not None:
            raise self.exception
        shutil.copy(src=self.file, dst=path)
        assert pkg is not None
        assert timeout == 120.0


class MockPkg():  # pylint: disable=too-few-public-methods
    """Mock Package."""

    def __init__(self, filename, project=None, version='1.2'):
        """Create MockPkg object."""
        self.filename = filename
        if project is None:
            self.project = filename
        else:
            self.project = project
        self.version = version


@pytest.mark.parametrize('fname,toname,licfnames,restxt',
                         [('pkgtest2.tar.gz', 'a.tar.gz',
                           ['a.txt'],
                           'This text is in a.txt 123\n'),
                          ('pkgtest2.tar.gz', 'b.tgz',
                           ['a.txt', 'subdir/c.md'],
                           'This text is in a.txt 123\n' +
                           'This text is in subdir/c.md 567\n'),
                          ('pkgtest2.tar.gz', 'c.tar.gz', None,
                           'This text is in b.md 345\n'),
                          ('pkgtest.zip', 'a.whl', ['a.txt'],
                           'This text is in a.txt 123\n'),
                          ('pkgtest.zip', 'b.zip', ['a.txt', 'subdir/c.md'],
                           'This text is in a.txt 123\n' +
                           'This text is in subdir/c.md 567\n'),
                          ('pkgtest.zip', 'c.zip', None,
                           'This text is in b.md 345\n',),])
def test_get_license_text_ok1(capsys,  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                              fname, toname, licfnames, restxt):
    """Test OK cases for get_license_text."""
    mclient = MockClient(file='test/test_pypkg_recdep/' + fname,
                         exception=None)
    mpkg = MockPkg(filename=toname)
    ret = get_license_text(client=mclient, pkg=mpkg, lic_files=licfnames)
    out, err = capsys.readouterr()
    assert restxt == ret
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('fname,licfnames,exc,pkg',
                         [('pkgtest2.tar.gz',
                           ['a.txt'], HTTPError('text 1'),
                           MockPkg(filename='a.tgz',
                                   project='pp', version='1.0')),
                          ('pkgtest2.tar.gz',
                           ['a.txt'], NoDigestsError('text 2'),
                           MockPkg(filename='a.tgz',
                                   project='p2', version='1.2'))])
def test_get_license_text_exc1(capsys, fname, licfnames, exc, pkg):
    """Test exception cases for get_license_text."""
    mclient = MockClient(file='test/test_pypkg_recdep/' + fname,
                         exception=deepcopy(exc))
    ret = get_license_text(client=mclient, pkg=deepcopy(pkg),
                           lic_files=licfnames)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == ret
    assert str(exc) in err
    assert f'Failed to download package {pkg.project} {pkg.version}' in err
    assert str(exc) in err


def test_get_license_text_nok1(capsys):
    """Test not OK case for get_license_text."""
    mclient = MockClient(file='test/test_pypkg_recdep/pkgtest2.tar.gz',
                         exception=None)
    mpkg = MockPkg(filename='a.txt')
    ret = get_license_text(client=mclient, pkg=deepcopy(mpkg),
                           lic_files=None)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == ret
    assert 'Do not know how to unpack a.txt\n' == err


@pytest.mark.parametrize('ver', ['3.12', '3.14'])
def test_get_environment_ok(capsys, ver):
    """Test OK cases of get_environment."""
    version = Version(ver)
    ret = get_environment(pyversion=version)
    out, err = capsys.readouterr()
    assert 'python_full_version' in ret
    assert ret['python_full_version'] == ver + '.0'
    assert 'python_version' in ret
    assert ret['python_version'] == ver
    assert 'os_name' in ret
    assert 'platform_machine' in ret
    assert '' == out
    assert '' == err


def test_get_requirements_ok1(capsys):
    """Test 1 get_rewuirememts from raw in stored file."""
    with open(file='test/test_pypkg_recdep/elt_raw.pkl', mode='rb') as file:
        raw = pickle.load(file=file)
        env = get_environment(pyversion=Version('3.13'))
        ret = get_requirements(raw=raw, pyenv=env)
        out, err = capsys.readouterr()
        assert '' == out
        assert '' == err
        assert len(ret) == 13
        assert ret[0].name == 'openpyxl'
        assert ret[0].specifier.contains(Version('3.1.5'))
        assert ret[1].name == 'types-openpyxl'
        assert ret[2].name == 'pylightxl'
        assert ret[3].name == 'XlsxWriter'
        assert ret[4].name == 'argcomplete'
        assert ret[5].name == 'pypi-simple'
        assert ret[6].name == 'requests'
        assert ret[7].name == 'types-requests'
        assert ret[8].name == 'packaging'
        assert ret[9].name == 'pip'
        assert ret[10].name == 'setuptools'
        assert ret[11].name == 'build'
        assert ret[12].name == 'wheel'
