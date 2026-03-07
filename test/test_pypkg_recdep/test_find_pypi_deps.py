#! /usr/local/bin/python3
"""Test finding dependencies in PyPI."""

# Copyright (c) 2025 Tom Björkholm
# MIT License
# pylint: disable=too-many-lines

from copy import deepcopy
from typing import NamedTuple, Optional, cast
from tempfile import TemporaryDirectory
import re
import shutil
import pickle
from tarfile import TarInfo
import pytest
from requests import HTTPError
from pypi_simple import PyPISimple, NoDigestsError, DistributionPackage, \
    ProjectPage, NoMetadataError, DigestMismatchError
from packaging.version import Version
from packaging.requirements import Requirement
from pypkg_recdep.pkg_info import Pkgs, PkgKey, PkgInfo
from pypkg_recdep.find_pypi_deps import select_given_lic_file, \
    select_default_lic_file, T, select_lic_file_names, \
    get_lic_text_zip, get_lic_text_tar, _fname_to_str, \
    get_license_text, get_environment, get_requirements, \
    find_fulfill_req, py_oks, NoMatchingPackage, meta_ok, \
    reset_warnings, _fix_invalid_version_specifier


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
def test_select_giv_lic1(capsys: pytest.CaptureFixture[str],  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                         intar: list[str], meta: list[str], res: list[str],
                         msgs: Optional[list[str]],
                         typ: type[AStr] | type[BStr],
                         pkgname: str) -> None:
    """Test OK cases of select_given_lic_file with string-based types."""
    files_in_tar = list(map(typ, deepcopy(intar)))
    ret = select_given_lic_file(files_in_tar=files_in_tar,
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
def test_select_giv_lic1_tarinfo(capsys: pytest.CaptureFixture[str],  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                                 intar: list[str], meta: list[str],
                                 res: list[str],
                                 msgs: Optional[list[str]],
                                 pkgname: str) -> None:
    """Test OK cases of select_given_lic_file with TarInfo."""
    files_in_tar = [TarInfo(name=elem) for elem in deepcopy(intar)]
    ret = select_given_lic_file(files_in_tar=files_in_tar,
                                meta_lic_files=deepcopy(meta),
                                pkgid=pkgname, _tinfo=TarInfo())
    assert len(res) == len(ret)
    retval: list[str] = []
    for retelem in ret:
        retval.append(_fname_to_str(retelem))
    assert retval == res
    out, err = capsys.readouterr()
    if ret:
        assert isinstance(ret[0], TarInfo)
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
def test_select_default_lic1(capsys: pytest.CaptureFixture[str],  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                             intar: list[str], res: list[str],
                             msgs: Optional[list[str]], pkgname: str,
                             typ: type[AStr] | type[BStr]) -> None:
    """Test OK cases of select_default_lic_file with string-based types."""
    files_in_tar = list(map(typ, deepcopy(intar)))
    ret = select_default_lic_file(files_in_tar=files_in_tar,
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
def test_select_default_lic1_tarinfo(capsys: pytest.CaptureFixture[str],  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                                     intar: list[str], res: list[str],
                                     msgs: Optional[list[str]],
                                     pkgname: str) -> None:
    """Test OK cases of select_default_lic_file with TarInfo."""
    files_in_tar = [TarInfo(name=elem) for elem in deepcopy(intar)]
    ret = select_default_lic_file(files_in_tar=files_in_tar,
                                  pkgid=pkgname, _tinfo=TarInfo())
    assert len(res) == len(ret)
    retval: list[str] = []
    for retelem in ret:
        retval.append(_fname_to_str(retelem))
    assert retval == res
    out, err = capsys.readouterr()
    if ret:
        assert isinstance(ret[0], TarInfo)
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
def test_select_liv_filnames1(capsys: pytest.CaptureFixture[str],  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                              monkeypatch: pytest.MonkeyPatch,
                              ftar: list[str], mlic: Optional[list[str]],
                              pkgi: str,
                              typ: type[AStr] | type[BStr],
                              given: bool) -> None:
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
        return []

    def sel_def_lic_file(files_in_tar: list[T],
                         pkgid: str, _tinfo: T) -> list[T]:
        """Mock select default lic file."""
        nonlocal def_called
        def_called += 1
        assert files_in_tar == ftar
        assert pkgid == pkgi
        assert _tinfo == typ('a')
        return []

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
def test_select_lic_filnames2(capsys: pytest.CaptureFixture[str],  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                              intar: list[str], meta: Optional[list[str]],
                              res: list[str], msgs: Optional[list[str]],
                              typ: type[AStr] | type[BStr],
                              pkgname: str) -> None:
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
def test_get_lic_test_zip(capsys: pytest.CaptureFixture[str],  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                          fname: str, licfnames: Optional[list[str]],
                          pkgid: str, restxt: str,
                          errtxt: str) -> None:
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
def test_get_lic_test_tar(capsys: pytest.CaptureFixture[str],  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                          fname: str, licfnames: Optional[list[str]],
                          pkgid: str, restxt: str,
                          errtxt: str) -> None:
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

    def __init__(self, file: str,
                 exception: Optional[Exception]) -> None:
        """Create a Mocked PYPISimple client object."""
        self.file = file
        self.exception = exception

    def download_package(self, pkg: DistributionPackage, path: str,
                         timeout: float) -> None:
        """Get a file as if was downloaded."""
        if self.exception is not None:
            raise self.exception
        shutil.copy(src=self.file, dst=path)
        assert pkg is not None
        assert timeout == 120.0


class MockPkg():  # pylint: disable=too-few-public-methods
    """Mock Package."""

    def __init__(self, filename: str, project: Optional[str] = None,
                 version: str = '1.2') -> None:
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
def test_get_license_text_ok1(capsys: pytest.CaptureFixture[str],  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                              fname: str, toname: str,
                              licfnames: Optional[list[str]],
                              restxt: str) -> None:
    """Test OK cases for get_license_text."""
    mclient = MockClient(file='test/test_pypkg_recdep/' + fname,
                         exception=None)
    mpkg = MockPkg(filename=toname)
    ret = get_license_text(client=cast(PyPISimple, mclient),
                           pkg=cast(DistributionPackage, mpkg),
                           lic_files=licfnames)
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
def test_get_license_text_exc1(capsys: pytest.CaptureFixture[str],
                               fname: str,
                               licfnames: list[str],
                               exc: Exception, pkg: MockPkg) -> None:
    """Test exception cases for get_license_text."""
    mclient = MockClient(file='test/test_pypkg_recdep/' + fname,
                         exception=deepcopy(exc))
    ret = get_license_text(client=cast(PyPISimple, mclient),
                           pkg=cast(DistributionPackage, deepcopy(pkg)),
                           lic_files=licfnames)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == ret
    assert str(exc) in err
    assert f'Failed to download package {pkg.project} {pkg.version}' in err
    assert str(exc) in err


def test_get_license_text_nok1(capsys: pytest.CaptureFixture[str]) -> None:
    """Test not OK case for get_license_text."""
    mclient = MockClient(file='test/test_pypkg_recdep/pkgtest2.tar.gz',
                         exception=None)
    mpkg = MockPkg(filename='a.txt')
    ret = get_license_text(client=cast(PyPISimple, mclient),
                           pkg=cast(DistributionPackage, deepcopy(mpkg)),
                           lic_files=None)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == ret
    assert 'Do not know how to unpack a.txt\n' == err


@pytest.mark.parametrize('ver', ['3.13', '3.14'])
def test_get_environment_ok(capsys: pytest.CaptureFixture[str],
                            ver: str) -> None:
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


def test_get_requirements_ok1(capsys: pytest.CaptureFixture[str]) -> None:
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


def test_get_requirements_ok2(capsys: pytest.CaptureFixture[str]) -> None:
    """Test 2 get_rewuirememts from raw in stored file."""
    with open(file='test/test_pypkg_recdep/jai_raw.pkl', mode='rb') as file:
        raw = pickle.load(file=file)
        env = get_environment(pyversion=Version('3.13'))
        ret = get_requirements(raw=raw, pyenv=env)
        out, err = capsys.readouterr()
        assert '' == out
        assert '' == err
        assert len(ret) == 2
        assert ret[0].name == 'more_itertools'
        assert not ret[0].specifier.contains(Version('3.1.5'))
        assert ret[0].specifier.contains(Version('4.1.5'))
        assert ret[1].name == 'inflect'


def test_get_requirements_ok3(capsys: pytest.CaptureFixture[str]) -> None:
    """Test 3 get_rewuirememts from raw in stored file."""
    with open(file='test/test_pypkg_recdep/pyt_raw.pkl', mode='rb') as file:
        raw = pickle.load(file=file)
        env = get_environment(pyversion=Version('3.13'))
        ret = get_requirements(raw=raw, pyenv=env)
        out, err = capsys.readouterr()
        assert '' == out
        assert '' == err
        assert len(ret) == 4
        assert ret[0].name == 'iniconfig'
        assert not ret[0].specifier.contains(Version('0.1.5'))
        assert ret[0].specifier.contains(Version('1.1.5'))
        assert ret[1].name == 'packaging'
        assert ret[2].name == 'pluggy'
        assert not ret[2].specifier.contains(Version('0.1.5'))
        assert ret[2].specifier.contains(Version('1.5.5'))
        assert not ret[2].specifier.contains(Version('2.1.5'))
        assert ret[3].name == 'pygments'


def test_get_requirements_ok4(capsys: pytest.CaptureFixture[str]) -> None:
    """Test 4 get_rewuirememts from raw in stored file."""
    with open(file='test/test_pypkg_recdep/pyt_raw.pkl', mode='rb') as file:
        raw = pickle.load(file=file)
        env = get_environment(pyversion=Version('3.10'))
        ret = get_requirements(raw=raw, pyenv=env)
        out, err = capsys.readouterr()
        assert '' == out
        assert '' == err
        assert len(ret) == 6
        assert ret[0].name == 'exceptiongroup'
        assert ret[1].name == 'iniconfig'
        assert not ret[1].specifier.contains(Version('0.1.5'))
        assert ret[1].specifier.contains(Version('1.1.5'))
        assert ret[2].name == 'packaging'
        assert ret[3].name == 'pluggy'
        assert not ret[3].specifier.contains(Version('0.1.5'))
        assert ret[3].specifier.contains(Version('1.5.5'))
        assert not ret[3].specifier.contains(Version('2.1.5'))
        assert ret[4].name == 'pygments'
        assert ret[5].name == 'tomli'


def test_get_requirements_ok5(capsys: pytest.CaptureFixture[str]) -> None:
    """Test 5 get_rewuirememts from raw in stored file."""
    with open(file='test/test_pypkg_recdep/elt_raw.pkl', mode='rb') as file:
        raw = pickle.load(file=file)
        del raw['requires_dist']
        env = get_environment(pyversion=Version('3.13'))
        ret = get_requirements(raw=raw, pyenv=env)
        out, err = capsys.readouterr()
        assert '' == out
        assert '' == err
        assert len(ret) == 0


def test_get_requirements_ok6(capsys: pytest.CaptureFixture[str]) -> None:
    """Test 6 get_rewuirememts from raw in stored file."""
    with open(file='test/test_pypkg_recdep/elt_raw.pkl', mode='rb') as file:
        raw = pickle.load(file=file)
        raw['requires_dist'] = []
        env = get_environment(pyversion=Version('3.13'))
        ret = get_requirements(raw=raw, pyenv=env)
        out, err = capsys.readouterr()
        assert '' == out
        assert '' == err
        assert len(ret) == 0


def test_get_requirements_ok7(capsys: pytest.CaptureFixture[str]) -> None:
    """Test 7 get_rewuirememts from raw in stored file."""
    with open(file='test/test_pypkg_recdep/jai_raw.pkl', mode='rb') as file:
        raw = pickle.load(file=file)
        raw['requires_dist'].insert(0, 'some strange text')
        env = get_environment(pyversion=Version('3.13'))
        ret = get_requirements(raw=raw, pyenv=env)
        out, err = capsys.readouterr()
        assert '' == out
        assert 'Ignoring invalid requirement: some strange text' in err
        assert 'Expected semicolon' in err
        assert 'or end' in err
        assert len(ret) == 2
        assert ret[0].name == 'more_itertools'
        assert not ret[0].specifier.contains(Version('3.1.5'))
        assert ret[0].specifier.contains(Version('4.1.5'))
        assert ret[1].name == 'inflect'


@pytest.mark.parametrize('req,pkgs,res',
                         [('foo <= 3.2', [('foo', '4.0.2'),
                                          ('bar', '2.0'),
                                          ('foo', '3.1.5')],
                           ('foo', '3.1.5')),
                          ('foo >= 3.2', [('foo', '4.0.2'),
                                          ('bar', '2.0'),
                                          ('foo', '3.1.5')],
                           ('foo', '4.0.2')),
                          ('bar', [('foo', '4.0.2'),
                                   ('bar', '2.0'),
                                   ('foo', '3.1.5')],
                           ('bar', '2.0')),
                          ('foo >= 5.2', [('foo', '4.0.2'),
                                          ('bar', '2.0'),
                                          ('foo', '3.1.5')],
                           None)])
def test_find_fullfill_req_ok1(capsys: pytest.CaptureFixture[str], req: str,
                               pkgs: list[tuple[str, str]],
                               res: Optional[tuple[str, str]]) -> None:
    """Test 1 of OK cases of find_fullfill_req."""
    packages: Pkgs = {}
    for name, ver in deepcopy(pkgs):
        key = PkgKey(name=deepcopy(name), version=deepcopy(ver))
        info = cast(PkgInfo, {'key': key})
        packages[key] = info
    ret = find_fulfill_req(req=Requirement(deepcopy(req)), pkgs=packages)
    out, err = capsys.readouterr()
    if res is not None:
        retkey = PkgKey(name=deepcopy(res[0]), version=deepcopy(res[1]))
        assert ret == retkey
    else:
        assert ret is None
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('pkgs,ver,res',
                         [([('ab', '2.3.4', '< 3.12')],
                           '3.11',
                           [('ab', '2.3.4')]),
                          ([('bc', '3.4', None)],
                           '3.11',
                           [('bc', '3.4')]),
                          ([('cd', '2.4', '')],
                           '3.11',
                           [('cd', '2.4')]),
                          ([('ab', '2.3.4', '< 3.12'),
                            ('cd', '4.1', '>= 3.13'),
                            ('ef', '5.2', None)],
                           '3.10',
                           [('ab', '2.3.4'),
                            ('ef', '5.2')])])
def test_pyoks_ok1(capsys: pytest.CaptureFixture[str],
                   pkgs: list[tuple[str, str, Optional[str]]], ver: str,
                   res: list[tuple[str, str]]) -> None:
    """Test variation 1 OK cases for py_oks."""
    dist_list: list[DistributionPackage] = []
    for (pname, pver, pyreq) in deepcopy(pkgs):
        dist_list.append(DistributionPackage(filename='fname', url='url',
                                             project=pname, version=pver,
                                             requires_python=pyreq,
                                             package_type='whl', digests={},
                                             has_sig=False))
    ret = py_oks(pkgs=dist_list, pyversion=Version(ver))
    out, err = capsys.readouterr()
    assert len(ret) == len(res)
    for retelem, reselem in zip(ret, deepcopy(res)):
        assert retelem.project == reselem[0]
        assert retelem.version == reselem[1]
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('pkgs,ver',
                         [([('ab', '2.3.4', '< 3.12')],
                           '3.13'),
                          ([('cd', '3.4.5', '>= 3.12')],
                           '3.10')])
def test_pyoks_nok1(capsys: pytest.CaptureFixture[str],
                    pkgs: list[tuple[str, str, Optional[str]]],
                    ver: str) -> None:
    """Test variation 1 not OK cases for py_oks."""
    dist_list: list[DistributionPackage] = []
    p_name: Optional[str] = None
    for (pname, pver, pyreq) in deepcopy(pkgs):
        p_name = pname
        dist_list.append(DistributionPackage(filename='fname', url='url',
                                             project=pname, version=pver,
                                             requires_python=pyreq,
                                             package_type='whl', digests={},
                                             has_sig=False))
    with pytest.raises(NoMatchingPackage) as exc:
        _ = py_oks(pkgs=dist_list, pyversion=Version(ver))
    assert f'No package of {p_name} that can run on Python version {ver}.' in \
        str(exc)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('spec,expected',
                         [('>=3.5.*', '>=3.5'),
                          ('<=3.5.*', '<=3.5'),
                          ('>3.5.*', '>3.5'),
                          ('<3.5.*', '<3.5'),
                          ('>=3.5.*, <4.*', '>=3.5, <4'),
                          ('>=3.5.1.*', '>=3.5.1'),
                          ('==3.5.*', '==3.5.*'),  # Should NOT be changed
                          ('!=3.5.*', '!=3.5.*'),  # Should NOT be changed
                          ('>=3.5', '>=3.5'),  # No change needed
                          ('>=3.5, <4.0', '>=3.5, <4.0')])  # No change needed
def test_fix_invalid_version_specifier(capsys: pytest.CaptureFixture[str],
                                       spec: str, expected: str) -> None:
    """Test _fix_invalid_version_specifier helper function."""
    result = _fix_invalid_version_specifier(spec)
    out, err = capsys.readouterr()
    assert result == expected
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('pkgs,ver,exp_vers',
                         [([('ab', '1.0', '>=3.5.*'),
                            ('ab', '2.0', '>=3.10')],
                           '3.13',
                           ['1.0', '2.0']),
                          ([('cd', '1.0', '>=3.5, <4.*')],
                           '3.12',
                           ['1.0'])])
def test_pyoks_fixable_requires_python(
        capsys: pytest.CaptureFixture[str],
        pkgs: list[tuple[str, str, Optional[str]]], ver: str,
        exp_vers: list[str]) -> None:
    """Test py_oks with fixable requires_python (PEP 440 violations).

    Some older packages have invalid version specifiers like '>=3.5.*'
    which violate PEP 440 (the .* suffix only works with == or !=).
    For >=, <=, >, < operators, >=3.5.* is equivalent to >=3.5.
    The function should fix these and NOT print a warning.
    """
    reset_warnings()
    dist_list: list[DistributionPackage] = []
    for (pname, pver, pyreq) in deepcopy(pkgs):
        dist_list.append(DistributionPackage(filename='fname', url='url',
                                             project=pname, version=pver,
                                             requires_python=pyreq,
                                             package_type='whl', digests={},
                                             has_sig=False))
    ret = py_oks(pkgs=dist_list, pyversion=Version(ver))
    out, err = capsys.readouterr()
    assert '' == out
    # Should NOT have printed a warning (the specifier was fixed)
    assert '' == err
    # Expected packages should be included
    ret_vers = [pkg.version for pkg in ret]
    for exp_ver in exp_vers:
        assert exp_ver in ret_vers


@pytest.mark.parametrize('pkgs,ver,exp_vers',
                         [([('ab', '1.0', '>=3..5')],  # Double dot - invalid
                           '3.13',
                           ['1.0']),
                          ([('cd', '1.0', '>=3.5, invalid')],  # Invalid part
                           '3.13',
                           ['1.0'])])
def test_pyoks_truly_invalid_requires_python(
        capsys: pytest.CaptureFixture[str],
        pkgs: list[tuple[str, str, Optional[str]]], ver: str,
        exp_vers: list[str]) -> None:
    """Test py_oks with truly invalid requires_python.

    For specifiers that cannot be fixed, include optimistically with warning.
    """
    reset_warnings()
    dist_list: list[DistributionPackage] = []
    for (pname, pver, pyreq) in deepcopy(pkgs):
        dist_list.append(DistributionPackage(filename='fname', url='url',
                                             project=pname, version=pver,
                                             requires_python=pyreq,
                                             package_type='whl', digests={},
                                             has_sig=False))
    ret = py_oks(pkgs=dist_list, pyversion=Version(ver))
    out, err = capsys.readouterr()
    assert '' == out
    # Should have printed a warning about invalid requires_python
    assert 'Warning:' in err
    assert 'invalid requires_python' in err
    # All packages should be included (optimistic handling)
    ret_vers = [pkg.version for pkg in ret]
    for exp_ver in exp_vers:
        assert exp_ver in ret_vers


@pytest.mark.parametrize('pyver,pkgvers',
                         [('3.10', ['0.7.9', '0.8.0']),
                          ('3.11', ['0.5', '0.7.10', '0.8.1']),
                          ('3.12', ['0.5', '0.7.11', '0.8.2', '0.8.4']),
                          ('3.13', ['0.5', '0.6', '0.6.2', '0.7.0',
                                    '0.7.1', '0.7.3', '0.7.5',
                                    '0.7.13', '0.8.3', '0.8.5'])])
def test_pyoks_ok2(capsys: pytest.CaptureFixture[str], pyver: str,
                   pkgvers: list[str]) -> None:
    """Test variation 2 OK cases for py_oks."""
    with open(file='test/test_pypkg_recdep/elt_page.pkl', mode='rb') as file:
        project_page: ProjectPage = pickle.load(file=file)
        ret = py_oks(pkgs=project_page.packages, pyversion=Version(pyver))
        out, err = capsys.readouterr()
        for pkg in ret:
            assert pkg.version in pkgvers
        retvers = [pkg.version for pkg in ret]
        for elemver in retvers:
            assert elemver in pkgvers
        for ver in pkgvers:
            assert ver in retvers
        assert '' == out
        assert '' == err


@pytest.mark.parametrize('pyver', ['3.9', '2.7'])
def test_pyoks_nok2(capsys: pytest.CaptureFixture[str], pyver: str) -> None:
    """Test variation 2 not OK cases for py_oks."""
    with open(file='test/test_pypkg_recdep/elt_page.pkl', mode='rb') as file:
        project_page: ProjectPage = pickle.load(file=file)
        with pytest.raises(NoMatchingPackage) as exc:
            _ = py_oks(pkgs=project_page.packages, pyversion=Version(pyver))
        assert 'No package of excel_list_transform that can run on Python ' + \
            f'version {pyver}.' in str(exc)
        out, err = capsys.readouterr()
        assert '' == out
        assert '' == err


@pytest.mark.parametrize('page', ['elt', 'jai', 'pyt'])
@pytest.mark.parametrize('pyver', ['3.10', '3.13'])
def test_pyoks_ok3(capsys: pytest.CaptureFixture[str], page: str,
                   pyver: str) -> None:
    """Test variation 3 OK cases for py_oks."""
    fname = 'test/test_pypkg_recdep/' + deepcopy(page) + '_page.pkl'
    with open(file=fname, mode='rb') as file:
        project_page: ProjectPage = pickle.load(file=file)
        ret = py_oks(pkgs=project_page.packages, pyversion=Version(pyver))
        out, err = capsys.readouterr()
        assert ret is not None
        assert len(ret) > 0
        assert '' == out
        assert '' == err


@pytest.mark.parametrize('page', ['elt'])
@pytest.mark.parametrize('pyver', ['3.1', '2.7'])
def test_pyoks_nok3(capsys: pytest.CaptureFixture[str], page: str,
                    pyver: str) -> None:
    """Test variation 3 not OK cases for py_oks."""
    fname = 'test/test_pypkg_recdep/' + deepcopy(page) + '_page.pkl'
    with open(file=fname, mode='rb') as file:
        project_page: ProjectPage = pickle.load(file=file)
        with pytest.raises(NoMatchingPackage) as exc:
            _ = py_oks(pkgs=project_page.packages, pyversion=Version(pyver))
        assert 'No package of excel_list_transform that can run on ' + \
            f'Python version {pyver}.' in str(exc)
        out, err = capsys.readouterr()
        assert '' == out
        assert '' == err


def get_fake_pkglist(pkl_base_name: str,
                     has_meta: list[bool]) -> list[DistributionPackage]:
    """Get a fake list of packages."""
    fname = 'test/test_pypkg_recdep/' + deepcopy(pkl_base_name) + '_page.pkl'
    ret: list[DistributionPackage] = []
    with open(file=fname, mode='rb') as file:
        page: ProjectPage = pickle.load(file=file)
        pkg_index = 0
        for what_meta in has_meta:
            if pkg_index >= len(page.packages):
                pkg_index = 0
            pkg = deepcopy(page.packages[pkg_index])
            pkg.has_metadata = what_meta
            ret.append(pkg)
            pkg_index += 1
        return ret


class MockMetaSpec(NamedTuple):
    """Spec for one metadata."""

    pkl_base: str
    metaver: Optional[str]
    exception: Optional[Exception]


class MockMetaClient():  # pylint: disable=too-few-public-methods
    """Moch PyPISimple to get fake metadata."""

    def __init__(self, spec: list[MockMetaSpec]) -> None:
        """Construct a MockMetaClient object."""
        self.spec: list[MockMetaSpec] = spec

    def get_package_metadata(self, pkg: DistributionPackage,
                             timeout: float = 30.0) -> str:
        """Get a fake metadata string object."""
        assert pkg is not None
        assert timeout is not None
        if not self.spec:
            raise NoMetadataError(filename='x.whl', url='http://a.com')
        if len(self.spec) < 1:
            raise NoMetadataError(filename='x.whl', url='http://a.com')
        this_spec = self.spec.pop(0)
        if this_spec.exception is not None:
            raise this_spec.exception
        fname = 'test/test_pypkg_recdep/' + deepcopy(this_spec.pkl_base) + \
            '_meta.pkl'
        with open(file=fname, mode='rb') as file:
            meta: str = pickle.load(file=file)
        if this_spec.metaver is None:
            return re.sub(r'Metadata-Version:[0-9. ]*\n', '', meta,
                          flags=re.IGNORECASE)
        return re.sub(r'Metadata-Version:[0-9. ]*\n',
                      'Metadata-Version: ' + this_spec.metaver + '\n',
                      meta,
                      flags=re.IGNORECASE)


DIG_MIS_ERROR = DigestMismatchError(algorithm='a', expected_digest='1234',
                                    actual_digest='123', url='http://a.com')
NO_DIG_ERROR = NoDigestsError(url='http://a.com')
HTTP_ERROR = HTTPError()
NO_META_ERROR = NoMetadataError(filename='a.txt', url='http://a.com')


@pytest.mark.parametrize('has_metas,page_pkl,mspecs,mver,msgs,retstart',
                         [([False, False], 'elt',
                           [], None, None, None),
                          ([True, True], 'elt',
                           [MockMetaSpec('elt', '2.4', None),
                            MockMetaSpec('elt', '2.2', None)],
                           Version('2.3'),
                           ['Warning:', 'exceeds the specified maximum'],
                           'Metadata-Version: 2.2'),
                          ([True, True], 'elt',
                           [MockMetaSpec('elt', '2.4', None),
                            MockMetaSpec('elt', '2.2', None)], None,
                           None, 'Metadata-Version: 2.4'),
                          ([True, True], 'elt',
                           [MockMetaSpec('elt', None, None),
                            MockMetaSpec('elt', '2.2', None)],
                           Version('2.3'),
                           None, 'Metadata-Version: 2.2'),
                          ([True, True], 'elt',
                           [MockMetaSpec('elt', None, None),
                            MockMetaSpec('elt', '2.4', None)],
                           Version('2.3'),
                           ['Warning:', 'exceeds the specified maximum'],
                           None),
                          ([True, True], 'elt',
                           [MockMetaSpec('elt', None, DIG_MIS_ERROR),
                            MockMetaSpec('elt', '2.2', None)],
                           Version('2.3'),
                           ['Failed to get metadata for excel_list_transform',
                            'a digest of'],
                           'Metadata-Version: 2.2'),
                          ([True, True], 'elt',
                           [MockMetaSpec('elt', None, NO_DIG_ERROR),
                            MockMetaSpec('elt', '2.2', None)],
                           Version('2.3'),
                           ['Failed to get metadata for excel_list_transform',
                            'No digests'],
                           'Metadata-Version: 2.2'),
                          ([True, True], 'elt',
                           [MockMetaSpec('elt', None, HTTP_ERROR),
                            MockMetaSpec('elt', '2.2', None)],
                           Version('2.3'),
                           ['Failed to get metadata for excel_list_transform'],
                           'Metadata-Version: 2.2'),
                          ([True, True], 'elt',
                           [MockMetaSpec('elt', None, NO_META_ERROR),
                            MockMetaSpec('elt', '2.2', None)],
                           Version('2.3'),
                           ['Failed to get metadata for excel_list_transform',
                            'No distribution metadata found'],
                           'Metadata-Version: 2.2')])
def test_meta_ok_ok1(capsys: pytest.CaptureFixture[str],  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                     has_metas: list[bool], page_pkl: str,
                     mspecs: list[MockMetaSpec], mver: Optional[Version],
                     msgs: Optional[list[str]],
                     retstart: Optional[str]) -> None:
    """Test first OK cases of meta_ok."""
    reset_warnings()
    mock = MockMetaClient(spec=mspecs)
    pkgs = get_fake_pkglist(pkl_base_name=page_pkl, has_meta=has_metas)
    metaversion = mver
    _, res = meta_ok(client=cast(PyPISimple, mock), pkgs=pkgs,
                     metaversion=metaversion)
    out, err = capsys.readouterr()
    if not retstart:
        assert not res
    else:
        assert res.startswith(retstart)
    assert '' == out
    if msgs is None:
        assert '' == err
    else:
        for msg in msgs:
            assert msg in err


@pytest.mark.parametrize('has_metas,page_pkl,mspecs,mver',
                         [([True, True], 'elt',
                           [MockMetaSpec('elt', '2.4', None),
                            MockMetaSpec('elt', '2.6', None)],
                           Version('2.3'))])
def test_meta_ok_nok1(capsys: pytest.CaptureFixture[str],  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                      has_metas: list[bool], page_pkl: str,
                      mspecs: list[MockMetaSpec],
                      mver: Optional[Version]) -> None:
    """Test first not OK cases of meta_ok."""
    reset_warnings()
    mock = MockMetaClient(spec=mspecs)
    pkgs = get_fake_pkglist(pkl_base_name=page_pkl, has_meta=has_metas)
    metaversion = mver
    with pytest.raises(NoMatchingPackage) as exc:
        _, _2 = meta_ok(client=cast(PyPISimple, mock), pkgs=pkgs,
                        metaversion=metaversion)
    out, err = capsys.readouterr()
    assert 'No packages of excel_list_transform have OK' in str(exc)
    assert '' == out
    # Warning about metadata version exceeding max should be printed
    assert 'Warning:' in err
