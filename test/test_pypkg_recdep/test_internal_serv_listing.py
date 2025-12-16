#! /usr/local/bin/python3
"""Test listing of content in internal PyPI."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

from copy import deepcopy
from typing import Optional
import re
import csv
from tempfile import TemporaryDirectory
import pytest
from packaging.version import Version
from pypi_simple import IndexPage, ProjectPage, DistributionPackage, \
    NoMetadataError, NoDigestsError, DigestMismatchError
from requests.auth import AuthBase
import requests
from get_example_pypi_list_data import load_example_pypi_list_data
from pypkg_recdep.pkg_info import PkgKey, MockListData
from pypkg_recdep.internal_server_listing import NoAuth, TokenAuth, \
    read_token_from_file, get_auth, get_meta, store_pkg, \
    list_for_projects, list_in_internal_server


class MockListClient:
    """Mock PyPISimple client for listing content in internal PyPI.

    The example data is given as an argument or loaded from a pickle
    file stored in git, and filtered to suit the test needs.
    This means that repeated calls with same arguments will return the
    same data. Several instances created with same arguments will produce
    the same data.
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self,
                 project_pattern: Optional[str] = None,
                 max_num_versions: Optional[int] = None,
                 endpoint: Optional[str] = None,
                 auth: Optional[AuthBase] = None,
                 data: Optional[MockListData] = None,
                 index_exception: Optional[Exception] = None,
                 project_exception: Optional[Exception] = None,
                 package_meta_exception: Optional[Exception] = None):
        """Create a MockListClient object.

        @param project_pattern  A regular expression to filter the projects.
                                If None, no filtering is applied and all
                                known projects are available.
        @param max_num_versions The maximum number of versions to return.
        @param endpoint         The endpoint to use for the PyPISimple client.
                                Not used in this mock client.
        @param auth             The authentication to use for the PyPISimple
                                client. If None, no authentication is used.
                                Not used in this mock client.
        @param data             The data to use for the mock client.
                                If None, the example data is loaded from
                                pickle file stored in git.
        @param index_exception  Exception to raise when get_index_page is
                                called.
        @param project_exception Exception to raise when get_project_page is
                                called.
        @param package_meta_exception Exception to raise when
                                get_package_metadata is called.
        """
        if endpoint is not None:
            assert isinstance(endpoint, str)
        if auth is not None:
            assert isinstance(auth, AuthBase)
        self.index_exception = index_exception
        self.project_exception = project_exception
        self.package_meta_exception = package_meta_exception
        self.mock_data: MockListData = \
            data if data is not None else load_example_pypi_list_data()
        self.project_pattern = project_pattern
        if self.project_pattern:
            self.mock_data.idx_page.projects = \
                [proj for proj in self.mock_data.idx_page.projects
                 if re.match(self.project_pattern, proj)]
        self.max_num_versions = max_num_versions

    def get_index_page(self, timeout: float = 30.0) -> IndexPage:
        """Get a fake index page."""
        assert timeout is not None
        if self.index_exception is not None:
            raise self.index_exception
        return self.mock_data.idx_page

    def get_project_page(self, project: str,
                         timeout: float = 30.0) -> ProjectPage:
        """Get a fake project page."""
        assert timeout is not None
        if self.project_exception is not None:
            raise self.project_exception
        if self.max_num_versions:
            orig_pkgs = self.mock_data.project_pages[project].packages
            pkgs = deepcopy(orig_pkgs)
            pkgs = sorted(pkgs, key=lambda x: Version(x.version)
                          if x.version else Version('0'),
                          reverse=True)
            pkgs = pkgs[:self.max_num_versions]
            self.mock_data.project_pages[project].packages = pkgs
        return self.mock_data.project_pages[project]

    def get_package_metadata(self, pkg=None,
                             timeout: float = 30.0) -> str:
        """Get a fake package metadata."""
        assert timeout is not None
        assert pkg is not None
        if self.package_meta_exception is not None:
            raise self.package_meta_exception
        key = PkgKey(pkg.project, pkg.version)
        return self.mock_data.metas[key]

    def __enter__(self) -> 'MockListClient':
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager."""


# Test that load_example_pypi_list_data() works as expected.


def test_load_example_pypi_list_data() -> None:
    """Test that load_example_pypi_list_data() works as expected."""
    example: MockListData = load_example_pypi_list_data()
    assert isinstance(example, MockListData)
    assert len(example.idx_page.projects) >= 20
    assert len(example.project_pages) >= 20
    assert len(example.metas) >= 20
    expected_pkg_num = {
        'excel-list-transform': 40,
        'jaraco.itertools': 75,
        'mypy': 1784,
        'pip': 275,
        'py-tes-estebanfs': 2,
        'pytesimal': 2,
        'pytesira': 22,
        'pyteslaapi': 12,
        'pyteslable': 6,
        'pytesmo': 320,
        'pytes-mock': 0,
        'Pytess': 2,
        'pytessel': 315,
        'PyTesser': 0,
        'pytesser3': 2,
        'pytesseract': 32,
        'py-tesseract': 3,
        'pytesseract-api': 10,
        'pytesseract-cli': 2,
        'pytesseraxcocr': 38,
        'pytessert': 1,
        'pytessng': 87,
        'pytesstrain': 34,
        'pytessy': 2,
        'pytest': 347
    }
    assert len(example.project_pages) == len(expected_pkg_num.keys())
    for project, expected_num in expected_pkg_num.items():
        assert project in example.project_pages
        assert len(example.project_pages[project].packages) == \
            expected_num
        for pkg in example.project_pages[project].packages:
            assert pkg.project.replace('-', '_').replace('.', '_') == \
                project.replace('-', '_').replace('.', '_')
            if pkg.has_metadata:
                pkgkey = PkgKey(pkg.project, pkg.version)
                assert pkgkey in example.metas
                assert example.metas[pkgkey] is not None


# Section with some tests of the MockListClient class.
# The reason for this is that when we use the MockListClient class to test
# the internal_server_listing module, we should not have to worry about
# the MockListClient class behaving in unexpected ways.


@pytest.mark.parametrize('project_pattern,max_num_versions,expected_count',
                         [(None, None, None),
                          ('pytest', None, 1),
                          ('^pyt', None, None),
                          (None, 5, None)])
def test_mock_list_client_init(
        capsys, project_pattern, max_num_versions, expected_count):
    """Test initialization of MockListClient."""
    client = MockListClient(project_pattern=project_pattern,
                            max_num_versions=max_num_versions)
    assert client.mock_data is not None
    assert isinstance(client.mock_data, MockListData)
    idx_page = client.get_index_page(timeout=30.0)
    if project_pattern:
        for proj in idx_page.projects:
            assert re.match(project_pattern, proj) is not None
    else:
        # When project_pattern is None, all projects should be available
        assert len(idx_page.projects) > 0
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    if expected_count is not None:
        assert len(idx_page.projects) == expected_count
    elif project_pattern == '^pyt':
        # Pattern '^pyt' should match multiple projects starting with 'pyt'
        assert len(idx_page.projects) > 0


@pytest.mark.parametrize('project,timeout, num_packages',
                         [('pytest', 30.0, 347),
                          ('pytest', 60.0, 347),
                          ('excel-list-transform', 30.0, 40)])
def test_mock_list_client_get_project_page(capsys, project, timeout,
                                           num_packages):
    """Test get_project_page method of MockListClient."""
    client = MockListClient()
    page = client.get_project_page(project=deepcopy(project), timeout=timeout)
    assert isinstance(page, ProjectPage)
    assert len(page.packages) == num_packages
    for pkg in page.packages:
        assert pkg.project.replace('-', '_').replace('.', '_') == \
            project.replace('-', '_').replace('.', '_')
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('project,max_num_versions',
                         [('pytest', 5),
                          ('pytest', 10),
                          ('excel-list-transform', 3)])
def test_mock_list_client_max_num_versions(capsys, project, max_num_versions):
    """Test max_num_versions parameter of MockListClient."""
    client = MockListClient(max_num_versions=max_num_versions)
    page = client.get_project_page(project=deepcopy(project), timeout=30.0)
    assert len(page.packages) == max_num_versions
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


def test_mock_list_client_get_package_metadata(capsys):
    """Test get_package_metadata method of MockListClient."""
    client = MockListClient()
    page = client.get_project_page(project='pytest', timeout=30.0)
    # Find a package with metadata
    pkg = None
    for p in page.packages:
        if p.has_metadata:
            pkg = p
            break
    if pkg is not None:
        meta = client.get_package_metadata(pkg=pkg, timeout=30.0)
        assert isinstance(meta, str)
        assert len(meta) > 0
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


def test_mock_list_client_context_manager(capsys):
    """Test MockListClient as context manager."""
    with MockListClient() as client:
        assert client is not None
        idx_page = client.get_index_page(timeout=30.0)
        assert idx_page is not None
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('endpoint',
                         ['http://test.com/simple', 'https://pypi.org/simple',
                          'http://localhost:8080/simple'])
def test_mock_list_client_endpoint(capsys, endpoint):
    """Test MockListClient with endpoint parameter."""
    client = MockListClient(endpoint=deepcopy(endpoint))
    assert client.mock_data is not None
    idx_page = client.get_index_page(timeout=30.0)
    assert idx_page is not None
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('auth',
                         [None, NoAuth(), TokenAuth('test-token')])
def test_mock_list_client_auth(capsys, auth):
    """Test MockListClient with auth parameter."""
    client = MockListClient(auth=auth)
    assert client.mock_data is not None
    idx_page = client.get_index_page(timeout=30.0)
    assert idx_page is not None
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


def test_mock_list_client_data(capsys):
    """Test MockListClient with custom data parameter."""
    custom_data = load_example_pypi_list_data()
    client = MockListClient(data=custom_data)
    assert client.mock_data is custom_data
    idx_page = client.get_index_page(timeout=30.0)
    assert idx_page is not None
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('exception',
                         [requests.HTTPError('test'),
                          ValueError('test error'),
                          RuntimeError('runtime error')])
def test_mock_list_client_index_exception(capsys, exception):
    """Test MockListClient with index_exception."""
    client = MockListClient(index_exception=exception)
    with pytest.raises(type(exception)):
        _ = client.get_index_page(timeout=30.0)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('exception',
                         [requests.HTTPError('test'),
                          ValueError('test error'),
                          KeyError('test')])
def test_mock_list_client_project_exception(capsys, exception):
    """Test MockListClient with project_exception."""
    client = MockListClient(project_exception=exception)
    with pytest.raises(type(exception)):
        _ = client.get_project_page(project='pytest', timeout=30.0)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('exception',
                         [NoMetadataError(filename='test.whl',
                                          url='http://test.com'),
                          NoDigestsError(url='http://test.com'),
                          requests.HTTPError('test')])
def test_mock_list_client_package_meta_exception(capsys, exception):
    """Test MockListClient with package_meta_exception."""
    client = MockListClient(package_meta_exception=exception)
    page = client.get_project_page(project='pytest', timeout=30.0)
    pkg = None
    for p in page.packages:
        if p.has_metadata:
            pkg = p
            break
    if pkg is not None:
        with pytest.raises(type(exception)):
            _ = client.get_package_metadata(pkg=pkg, timeout=30.0)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


# Section with tests of the internal_server_listing module.


class MockMetaClient:  # pylint: disable=too-few-public-methods
    """Mock client for testing get_meta with exceptions."""

    def __init__(self, exception: Optional[Exception] = None,
                 metadata: Optional[str] = None):
        """Create a MockMetaClient object.

        @param exception  Exception to raise when get_package_metadata is
                          called.
        @param metadata   Metadata string to return if no exception.
        """
        self.exception = exception
        self.metadata = metadata

    def get_package_metadata(self, pkg, timeout: float = 30.0) -> str:
        """Get package metadata or raise exception."""
        assert timeout is not None
        assert pkg is not None
        if self.exception is not None:
            raise self.exception
        if self.metadata is not None:
            return deepcopy(self.metadata)
        # Default metadata with metadata_version
        return 'Metadata-Version: 2.1\nName: test-package\nVersion: 1.0.0\n'


@pytest.mark.parametrize('has_metadata,metadata,expected',
                         [(False, None, 'unknown'),
                          (True, 'Metadata-Version: 2.1\nName: test\n',
                           '2.1'),
                          (True, 'Metadata-Version: 2.4\nName: test\n',
                           '2.4'),
                          (True, 'Metadata-Version: 1.0\nName: test\n',
                           '1.0')])
def test_get_meta_ok1(capsys, has_metadata, metadata, expected):
    """Test OK cases of get_meta."""
    pkg = DistributionPackage(filename='test.whl', url='http://test.com',
                              project='pytest', version='9.0.0',
                              requires_python=None, package_type='whl',
                              digests={}, has_sig=False)
    pkg.has_metadata = has_metadata
    if has_metadata:
        mock_client = MockMetaClient(metadata=deepcopy(metadata))
    else:
        mock_client = MockMetaClient()
    ret = get_meta(client=mock_client, pkg=pkg)
    assert ret == expected
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('project,ver,metaver',
                         [('pytest', '2.7.1', '2.0'),
                          ('excel-list-transform', '0.5', '2.1')])
def test_get_meta_with_mock_list_client(capsys, project, ver, metaver):
    """Test get_meta with MockListClient using real test data."""
    client = MockListClient()
    page = client.get_project_page(project=deepcopy(project), timeout=30.0)
    # Find a package with metadata
    pkg = [p for p in page.packages if p.version == ver][0]
    ret = get_meta(client=client, pkg=pkg)
    assert ret == metaver
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('metadata,expected',
                         [('Name: test\nVersion: 1.0.0\n', 'unknown'),
                          ('Metadata-Version: 2.1\nName: test\n', '2.1')])
def test_get_meta_no_metadata_version(capsys, metadata, expected):
    """Test get_meta when metadata_version is missing."""
    pkg = DistributionPackage(filename='test.whl', url='http://test.com',
                              project='pytest', version='9.0.0',
                              requires_python=None, package_type='whl',
                              digests={}, has_sig=False)
    pkg.has_metadata = True
    mock_client = MockMetaClient(metadata=deepcopy(metadata))
    ret = get_meta(client=mock_client, pkg=pkg)
    assert ret == expected
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('exception,err_msg',
                         [(NoMetadataError(filename='test.whl',
                                           url='http://test.com'),
                           'Failed to get metadata version for pytest'),
                          (NoDigestsError(url='http://test.com'),
                           'Failed to get metadata version for pytest'),
                          (DigestMismatchError(
                              algorithm='sha256', expected_digest='abc',
                              actual_digest='def', url='http://test.com'),
                           'Failed to get metadata version for pytest'),
                          (requests.HTTPError('test error'),
                           'Failed to get metadata version for pytest'),
                          (KeyError('test'),
                           'Failed to get metadata version for pytest'),
                          (ValueError('test'),
                           'Failed to get metadata version for pytest')])
def test_get_meta_exceptions(capsys, exception, err_msg):
    """Test get_meta with various exceptions using MockListClient."""
    client = MockListClient(package_meta_exception=exception)
    page = client.get_project_page(project='pytest', timeout=30.0)
    pkg = None
    for p in page.packages:
        if p.has_metadata:
            pkg = p
            break
    if pkg is not None:
        ret = get_meta(client=client, pkg=pkg)
        assert ret == 'unknown'
        out, err = capsys.readouterr()
        assert '' == out
        assert err_msg in err


@pytest.mark.parametrize('name,ver,meta,ptype,expected_dict',
                         [('pkg1', '1.0.0', '2.1', 'whl',
                           {'pkg1': {'1.0.0': {'meta': '2.1',
                                               'ptype': 'whl'}}}),
                          ('pkg2', '2.0.0', '2.4', 'sdist',
                           {'pkg2': {'2.0.0': {'meta': '2.4',
                                               'ptype': 'sdist'}}}),
                          ('pkg3', '3.0.0', 'unknown', None,
                           {'pkg3': {'3.0.0': {'meta': 'unknown',
                                               'ptype': 'unknown'}}})])
# pylint: disable=too-many-arguments,too-many-positional-arguments
def test_store_pkg_new_package(capsys, name, ver, meta, ptype, expected_dict):
    """Test store_pkg with new packages."""
    proj_pkgs: dict[str, dict[str, dict[str, str]]] = {}
    store_pkg(proj_pkgs=proj_pkgs, name=deepcopy(name), ver=deepcopy(ver),
              meta=deepcopy(meta), ptype=deepcopy(ptype))
    assert proj_pkgs == expected_dict
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('name,ver,meta,ptype,initial_dict,expected_dict',
                         [('pkg1', '2.0.0', '2.1', 'whl',
                           {'pkg1': {'1.0.0': {'meta': '2.1',
                                               'ptype': 'whl'}}},
                           {'pkg1': {'1.0.0': {'meta': '2.1',
                                               'ptype': 'whl'},
                                     '2.0.0': {'meta': '2.1',
                                               'ptype': 'whl'}}}),
                          ('pkg2', '2.0.0', '2.4', 'sdist',
                           {'pkg2': {'1.0.0': {'meta': '2.1',
                                               'ptype': 'whl'}}},
                           {'pkg2': {'1.0.0': {'meta': '2.1',
                                               'ptype': 'whl'},
                                     '2.0.0': {'meta': '2.4',
                                               'ptype': 'sdist'}}})])
# pylint: disable=too-many-arguments,too-many-positional-arguments
def test_store_pkg_new_version(
        capsys, name, ver, meta, ptype, initial_dict, expected_dict):
    """Test store_pkg with new version of existing package."""
    proj_pkgs = deepcopy(initial_dict)
    store_pkg(proj_pkgs=proj_pkgs, name=deepcopy(name), ver=deepcopy(ver),
              meta=deepcopy(meta), ptype=deepcopy(ptype))
    assert proj_pkgs == expected_dict
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('name,ver,meta,ptype,initial_dict,expected_dict',
                         [('pkg1', '1.0.0', '2.4', 'whl',
                           {'pkg1': {'1.0.0': {'meta': 'unknown',
                                               'ptype': 'whl'}}},
                           {'pkg1': {'1.0.0': {'meta': '2.4',
                                               'ptype': 'whl'}}}),
                          ('pkg2', '1.0.0', '2.1', 'sdist',
                           {'pkg2': {'1.0.0': {'meta': '2.1',
                                               'ptype': 'whl'}}},
                           {'pkg2': {'1.0.0': {'meta': '2.1',
                                               'ptype': 'whl + sdist'}}}),
                          ('pkg3', '1.0.0', '2.1', 'whl',
                           {'pkg3': {'1.0.0': {'meta': '2.1',
                                               'ptype': 'whl'}}},
                           {'pkg3': {'1.0.0': {'meta': '2.1',
                                               'ptype': 'whl'}}})])
# pylint: disable=too-many-arguments,too-many-positional-arguments
def test_store_pkg_existing_version(capsys, name, ver, meta, ptype,
                                    initial_dict, expected_dict):
    """Test store_pkg with existing package version."""
    proj_pkgs = deepcopy(initial_dict)
    store_pkg(proj_pkgs=proj_pkgs, name=deepcopy(name), ver=deepcopy(ver),
              meta=deepcopy(meta), ptype=deepcopy(ptype))
    assert proj_pkgs == expected_dict
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('name,ver,meta,ptype',
                         [(None, '1.0.0', '2.1', 'whl'),
                          ('pkg1', None, '2.1', 'whl'),
                          (None, None, '2.1', 'whl')])
def test_store_pkg_none_values(capsys, name, ver, meta, ptype):
    """Test store_pkg with None name or version."""
    proj_pkgs: dict[str, dict[str, dict[str, str]]] = {}
    initial_proj_pkgs = deepcopy(proj_pkgs)
    store_pkg(proj_pkgs=proj_pkgs, name=name, ver=ver, meta=deepcopy(meta),
              ptype=deepcopy(ptype))
    assert proj_pkgs == initial_proj_pkgs
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('token_content,expected',
                         [('mytoken123', 'mytoken123'),
                          ('  mytoken123  ', 'mytoken123'),
                          ('mytoken123\n', 'mytoken123'),
                          ('  mytoken123\n  ', 'mytoken123'),
                          ('token_with_underscores', 'token_with_underscores'),
                          ('token-with-dashes', 'token-with-dashes'),
                          ('token.with.dots', 'token.with.dots'),
                          ('', '')])
def test_read_token_from_file_ok1(capsys, token_content, expected):
    """Test OK cases of read_token_from_file."""
    with TemporaryDirectory() as dirname:
        token_file = dirname + '/token.txt'
        with open(token_file, 'w', encoding='utf-8') as file:
            file.write(deepcopy(token_content))
        ret = read_token_from_file(token_file=token_file)
        assert ret == expected
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('token_file',
                         ['/nonexistent/file/path/token.txt',
                          '/tmp/also/does/not/exist/token.txt'])
def test_read_token_from_file_nok1(capsys, token_file):
    """Test not OK cases of read_token_from_file with file not found."""
    with pytest.raises(FileNotFoundError):
        _ = read_token_from_file(token_file=deepcopy(token_file))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('pat_file,token_content,expected_type',
                         [('token.txt', 'mytoken123', TokenAuth),
                          ('token.txt', '  mytoken123  ', TokenAuth),
                          ('token.txt', 'another-token', TokenAuth),
                          ('', None, NoAuth)])
def test_get_auth_ok1(capsys, pat_file, token_content, expected_type):
    """Test OK cases of get_auth."""
    with TemporaryDirectory() as dirname:
        if pat_file and token_content is not None:
            token_file = dirname + '/' + deepcopy(pat_file)
            with open(token_file, 'w', encoding='utf-8') as file:
                file.write(deepcopy(token_content))
            ret = get_auth(pat_file=token_file)
        else:
            ret = get_auth(pat_file=deepcopy(pat_file))
        assert isinstance(ret, expected_type)
        if isinstance(ret, TokenAuth):
            expected_token = deepcopy(token_content).strip()
            assert ret.token == expected_token
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('pat_file',
                         ['/nonexistent/file/path/token.txt',
                          '/tmp/also/does/not/exist/token.txt'])
def test_get_auth_nok1(capsys, pat_file):
    """Test not OK cases of get_auth with file not found."""
    with pytest.raises(FileNotFoundError):
        _ = get_auth(pat_file=deepcopy(pat_file))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('projects',
                         [['pytest'],
                          ['excel-list-transform'],
                          ['pytest', 'excel-list-transform']])
def test_list_for_projects_ok1(capsys, projects):
    """Test OK cases of list_for_projects."""
    client = MockListClient()
    with TemporaryDirectory() as dirname:
        output_file = dirname + '/output.csv'
        list_for_projects(client=client, projects=deepcopy(projects),
                          output_file=output_file)
        with open(output_file, 'r', encoding='utf-8',
                  newline='') as file:
            reader = csv.reader(file, dialect='unix')
            rows = list(reader)
        assert len(rows) > 0
        assert rows[0] == ['Name', 'Version', 'Metadata Version',
                           'Formats']
        # Check that all projects are represented
        project_names = {row[0] for row in rows[1:]}
        for proj in projects:
            assert proj in project_names or \
                proj.replace('-', '_') in project_names
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('project,min_versions',
                         [('pytest', 100),
                          ('excel-list-transform', 10)])
def test_list_for_projects_content(capsys, project, min_versions):
    """Test content of list_for_projects output."""
    client = MockListClient()
    with TemporaryDirectory() as dirname:
        output_file = dirname + '/output.csv'
        list_for_projects(client=client,
                          projects=[deepcopy(project)],
                          output_file=output_file)
        with open(output_file, 'r', encoding='utf-8',
                  newline='') as file:
            reader = csv.reader(file, dialect='unix')
            rows = list(reader)
        assert len(rows) > min_versions
        # Check header
        assert rows[0] == ['Name', 'Version', 'Metadata Version',
                           'Formats']
        # Check data rows have 4 columns
        for row in rows[1:]:
            assert len(row) == 4
            assert row[0] is not None
            assert row[1] is not None
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('server_url,pat_file,limit',
                         [('http://test.com', '', None),
                          ('http://test.com', '', 5),
                          ('http://test.com/', '', 10)])
def test_list_in_internal_server_ok1(capsys, monkeypatch, server_url,
                                      pat_file, limit):
    """Test OK cases of list_in_internal_server."""
    client = MockListClient()

    class MockPyPISimple:
        """Mock PyPISimple class."""

        def __init__(self, endpoint, auth):
            """Initialize mock PyPISimple."""
            assert endpoint is not None
            assert auth is not None
            self.client = client

        def __enter__(self):
            """Enter context manager."""
            return self.client

        def __exit__(self, exc_type, exc_val, exc_tb):
            """Exit context manager."""
            return None

    monkeypatch.setattr(
        'pypkg_recdep.internal_server_listing.PyPISimple',
        MockPyPISimple)
    with TemporaryDirectory() as dirname:
        output_file = dirname + '/output.csv'
        list_in_internal_server(
            server_url=deepcopy(server_url), pat_file=deepcopy(pat_file),
            output_file=output_file, limit=limit)
        with open(output_file, 'r', encoding='utf-8',
                  newline='') as file:
            reader = csv.reader(file, dialect='unix')
            rows = list(reader)
        assert len(rows) > 0
        assert rows[0] == ['Name', 'Version', 'Metadata Version',
                           'Formats']
        if limit:
            # Limit applies to projects processed, not unique names
            # Just verify we have some output
            assert len(rows) > 1
    out, err = capsys.readouterr()
    if limit:
        assert f'limiting output to {limit} packages' in err
    assert '' == out


@pytest.mark.parametrize('server_url',
                         ['http://test.com', 'http://test.com/',
                          'https://example.org/pypi'])
def test_list_in_internal_server_urls(capsys, monkeypatch, server_url):
    """Test list_in_internal_server with different URL formats."""
    client = MockListClient()

    class MockPyPISimple:
        """Mock PyPISimple class."""

        def __init__(self, endpoint, auth):
            """Initialize mock PyPISimple."""
            assert endpoint.endswith('/simple')
            assert auth is not None
            self.client = client

        def __enter__(self):
            """Enter context manager."""
            return self.client

        def __exit__(self, exc_type, exc_val, exc_tb):
            """Exit context manager."""
            return None

    monkeypatch.setattr(
        'pypkg_recdep.internal_server_listing.PyPISimple',
        MockPyPISimple)
    with TemporaryDirectory() as dirname:
        output_file = dirname + '/output.csv'
        list_in_internal_server(
            server_url=deepcopy(server_url), pat_file='',
            output_file=output_file, limit=None)
        with open(output_file, 'r', encoding='utf-8',
                  newline='') as file:
            reader = csv.reader(file, dialect='unix')
            rows = list(reader)
        assert len(rows) > 0
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
