#! /usr/local/bin/python3
"""Test listing of content in internal PyPI."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

from copy import deepcopy
from typing import Optional
import re
from tempfile import TemporaryDirectory
import pytest
from packaging.version import Version
from pypi_simple import IndexPage, ProjectPage
from get_example_pypi_list_data import load_example_pypi_list_data
from pypkg_recdep.pkg_info import PkgKey, MockListData
from pypkg_recdep.internal_server_listing import NoAuth, TokenAuth, \
    read_token_from_file, get_auth


class MockListClient:
    """Mock PyPISimple client for listing content in internal PyPI.

    The example data is loaded from a pickle file stored in git,
    and filtered to suit the test needs. This means that repeated
    calls with same arguments will return the same data.
    Several instances created with same arguments will produce the same
    data.
    """

    def __init__(self,
                 project_pattern: Optional[str] = None,
                 max_num_versions: Optional[int] = None):
        """Create a MockListClient object.

        @param project_pattern  A regular expression to filter the projects.
        @param max_num_versions The maximum number of versions to return.
        """
        self.mock_data: MockListData = load_example_pypi_list_data()
        self.project_pattern = project_pattern
        if self.project_pattern:
            self.mock_data.idx_page.projects = \
                [proj for proj in self.mock_data.idx_page.projects
                 if re.match(self.project_pattern, proj)]
        self.max_num_versions = max_num_versions

    def get_index_page(self, timeout: float = 30.0) -> IndexPage:
        """Get a fake index page."""
        assert timeout is not None
        return self.mock_data.idx_page

    def get_project_page(self, project: str,
                         timeout: float = 30.0) -> ProjectPage:
        """Get a fake project page."""
        assert timeout is not None
        if self.max_num_versions:
            orig_pkgs = self.mock_data.project_pages[project].packages
            pkgs = deepcopy(orig_pkgs)
            pkgs = sorted(pkgs, key=lambda x: Version(x.version)
                          if x.version else Version('0'),
                          reverse=True)
            pkgs = pkgs[:self.max_num_versions]
            self.mock_data.project_pages[project].packages = pkgs
        return self.mock_data.project_pages[project]

    def get_package_metadata(self, package: str,
                             timeout: float = 30.0) -> str:
        """Get a fake package metadata."""
        assert timeout is not None
        key = PkgKey(package.project, package.version)
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


# Section with tests of the internal_server_listing module.


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
