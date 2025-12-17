#! /usr/local/bin/python3
"""Test listing of content in Azure DevOps PyPI."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

from copy import deepcopy
from tempfile import TemporaryDirectory
import csv
import base64
import pytest
from pypkg_recdep.list_ado_content import print_pkgs, get_headers, \
    get_from_rest, get_value_from_rest, get_feed_id, get_from_meta, \
    parse_meta, parse_fileinfo, get_pkg_versions, get_pkgs, \
    list_ado_content, UrlInfo, SinglePkgInfo, PkgInfo, \
    RestException, get_headers_per_file


class MockResponse:
    """Mock response object for requests.get."""

    def __init__(self, json_data, ok=True, status_code=200):
        """Create a MockResponse object.

        @param json_data  The JSON data to return.
        @param ok         Whether the response is OK.
        @param status_code The HTTP status code.
        """
        self.json_data = json_data
        self.ok = ok
        self.status_code = status_code

    def json(self):
        """Return the JSON data."""
        return self.json_data

    def __str__(self):
        """Return string representation."""
        return f'MockResponse({self.status_code})'


@pytest.mark.parametrize('pkgs,expected_rows',
                         [([PkgInfo(name='pkg1',
                                    versions=[
                                        SinglePkgInfo(
                                            name='pkg1',
                                            version='1.0.0',
                                            metadata_version='2.1',
                                            package_type='wheel',
                                            file_name='pkg1-1.0.0.whl')])],
                           [['Name', 'Name of version', 'Version',
                             'Metadata version', 'package type',
                             'file name'],
                            ['pkg1', 'pkg1', '1.0.0', '2.1', 'wheel',
                             'pkg1-1.0.0.whl']]),
                          ([PkgInfo(name='pkg2',
                                    versions=[
                                        SinglePkgInfo(
                                            name='pkg2',
                                            version='2.0.0',
                                            metadata_version='2.4',
                                            package_type='sdist',
                                            file_name='pkg2-2.0.0.tar.gz'),
                                        SinglePkgInfo(
                                            name='pkg2',
                                            version='2.1.0',
                                            metadata_version='2.4',
                                            package_type='wheel',
                                            file_name='pkg2-2.1.0.whl')])],
                           [['Name', 'Name of version', 'Version',
                             'Metadata version', 'package type',
                             'file name'],
                            ['pkg2', 'pkg2', '2.0.0', '2.4', 'sdist',
                             'pkg2-2.0.0.tar.gz'],
                            ['pkg2', 'pkg2', '2.1.0', '2.4', 'wheel',
                             'pkg2-2.1.0.whl']])])
def test_print_pkgs_ok1(capsys, pkgs, expected_rows):
    """Test OK cases of print_pkgs."""
    with TemporaryDirectory() as dirname:
        file_name = dirname + '/output.csv'
        print_pkgs(pkgs=deepcopy(pkgs), file_name=file_name)
        with open(file=file_name, mode='r', encoding='utf-8',
                  newline='') as file:
            reader = csv.reader(file, dialect='unix')
            rows = list(reader)
        assert rows == expected_rows
        out, err = capsys.readouterr()
        assert '' == out
        assert f'Wrote results to {file_name}' in err


def test_print_pkgs_empty(capsys):
    """Test print_pkgs with empty package list."""
    with TemporaryDirectory() as dirname:
        file_name = dirname + '/output.csv'
        print_pkgs(pkgs=[], file_name=file_name)
        with open(file=file_name, mode='r', encoding='utf-8',
                  newline='') as file:
            reader = csv.reader(file, dialect='unix')
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0] == ['Name', 'Name of version', 'Version',
                           'Metadata version', 'package type',
                           'file name']
        out, err = capsys.readouterr()
        assert '' == out
        assert f'Wrote results to {file_name}' in err


@pytest.mark.parametrize('pat_content,expected_auth',
                         [('mytoken123',
                           'Basic ' +
                           base64.b64encode(
                               ':mytoken123'.encode()).decode()),
                          ('test_token',
                           'Basic ' +
                           base64.b64encode(
                               ':test_token'.encode()).decode()),
                          ('abc-def-ghi',
                           'Basic ' +
                           base64.b64encode(
                               ':abc-def-ghi'.encode()).decode())])
def test_get_headers_ok1(capsys, pat_content, expected_auth):
    """Test OK cases of get_headers."""
    get_headers_per_file.clear()
    with TemporaryDirectory() as dirname:
        pat_file = dirname + '/pat.txt'
        with open(file=pat_file, mode='w', encoding='utf-8') as file:
            file.write(deepcopy(pat_content))
        headers = get_headers(pat_file=pat_file)
        assert 'Authorization' in headers
        assert headers['Authorization'] == expected_auth
        # Test cache
        headers2 = get_headers(pat_file=pat_file)
        assert headers2 is headers
        out, err = capsys.readouterr()
        assert '' == out
        assert '' == err


def test_get_headers_none(capsys):
    """Test get_headers with None pat_file."""
    headers = get_headers(pat_file=None)
    assert headers == {}
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


def test_get_headers_not_found(capsys):
    """Test get_headers with non-existent file."""
    with pytest.raises(SystemExit) as exc:
        _ = get_headers(pat_file='/nonexistent/file.txt')
    assert exc.value.code == 1
    out, err = capsys.readouterr()
    assert '' == out
    assert 'PAT file "/nonexistent/file.txt" not found' in err


@pytest.mark.parametrize('json_data,url',
                         [({'key': 'value'}, 'http://test.com/api'),
                          ({'value': [1, 2, 3]}, 'http://example.com'),
                          ({'name': 'test', 'version': '1.0'},
                           'https://test.org/api')])
def test_get_from_rest_ok1(capsys, monkeypatch, json_data, url):
    """Test OK cases of get_from_rest."""
    get_headers_per_file.clear()

    # pylint: disable=unused-argument
    def mock_get(url, headers, timeout, verify):
        """Mock requests.get."""
        assert timeout is not None
        assert verify is False
        assert headers is not None
        return MockResponse(json_data=deepcopy(json_data), ok=True)

    monkeypatch.setattr('requests.get', mock_get)
    with TemporaryDirectory() as dirname:
        pat_file = dirname + '/pat.txt'
        with open(file=pat_file, mode='w', encoding='utf-8') as file:
            file.write('test_token')
        ret = get_from_rest(url=deepcopy(url), pat_file=pat_file)
        assert ret == json_data
        out, err = capsys.readouterr()
        assert '' == out
        assert '' == err


@pytest.mark.parametrize('status_code,url',
                         [(404, 'http://test.com/api'),
                          (500, 'http://example.com'),
                          (403, 'https://test.org/api')])
def test_get_from_rest_nok1(capsys, monkeypatch, status_code, url):
    """Test not OK cases of get_from_rest."""
    get_headers_per_file.clear()

    # pylint: disable=unused-argument
    def mock_get(url, headers, timeout, verify):
        """Mock requests.get."""
        assert timeout is not None
        assert verify is False
        assert headers is not None
        return MockResponse(json_data={}, ok=False,
                            status_code=status_code)

    monkeypatch.setattr('requests.get', mock_get)
    with TemporaryDirectory() as dirname:
        pat_file = dirname + '/pat.txt'
        with open(file=pat_file, mode='w', encoding='utf-8') as file:
            file.write('test_token')
        with pytest.raises(RestException):
            _ = get_from_rest(url=deepcopy(url), pat_file=pat_file)
        out, err = capsys.readouterr()
        assert '' == out
        assert f'Failed REST request: {url}' in err


@pytest.mark.parametrize('value_data,url',
                         [([{'id': '1'}, {'id': '2'}],
                           'http://test.com/api'),
                          ([{'name': 'test'}], 'http://example.com'),
                          ([], 'https://test.org/api')])
def test_get_value_from_rest_ok1(capsys, monkeypatch, value_data, url):
    """Test OK cases of get_value_from_rest."""
    get_headers_per_file.clear()

    # pylint: disable=unused-argument
    def mock_get(url, headers, timeout, verify):
        """Mock requests.get."""
        assert timeout is not None
        assert verify is False
        assert headers is not None
        return MockResponse(
            json_data={'value': deepcopy(value_data)}, ok=True)

    monkeypatch.setattr('requests.get', mock_get)
    with TemporaryDirectory() as dirname:
        pat_file = dirname + '/pat.txt'
        with open(file=pat_file, mode='w', encoding='utf-8') as file:
            file.write('test_token')
        ret = get_value_from_rest(url=deepcopy(url), pat_file=pat_file)
        assert ret == value_data
        out, err = capsys.readouterr()
        assert '' == out
        assert '' == err


@pytest.mark.parametrize(
    'feeds_data,lookup_name,expected_id',
    [([{'fullyQualifiedName': 'packages', 'id': 'feed-id-123'}],
      'packages', 'feed-id-123'),
     ([{'fullyQualifiedName': 'test-feed', 'id': 'abc-def-123'},
       {'fullyQualifiedName': 'packages', 'id': 'xyz-789'}],
      'packages', 'xyz-789'),
     ([{'fullyQualifiedName': 'my-feed', 'id': 'id-1'}],
      'my-feed', 'id-1')])
def test_get_feed_id_ok1(capsys, monkeypatch, feeds_data, lookup_name,
                         expected_id):
    """Test OK cases of get_feed_id."""
    get_headers_per_file.clear()

    # pylint: disable=unused-argument
    def mock_get(url, headers, timeout, verify):
        """Mock requests.get."""
        assert timeout is not None
        assert verify is False
        assert headers is not None
        return MockResponse(
            json_data={'value': deepcopy(feeds_data)}, ok=True)

    monkeypatch.setattr('requests.get', mock_get)
    with TemporaryDirectory() as dirname:
        pat_file = dirname + '/pat.txt'
        with open(file=pat_file, mode='w', encoding='utf-8') as file:
            file.write('test_token')
        url_info = UrlInfo(instance='test.com', collection='col1',
                           pat_file=pat_file)
        ret = get_feed_id(url_info=url_info,
                          lookup_name=deepcopy(lookup_name))
        assert ret == expected_id
        out, err = capsys.readouterr()
        assert '' == out
        assert f'Found feed ID "{expected_id}"' in err


@pytest.mark.parametrize(
    'feeds_data,lookup_name',
    [([{'fullyQualifiedName': 'packages', 'id': 'feed-id-123'}],
      'nonexistent'),
     ([{'fullyQualifiedName': 'test-feed', 'id': 'abc-def-123'}],
      'packages')])
def test_get_feed_id_nok1(capsys, monkeypatch, feeds_data, lookup_name):
    """Test not OK cases of get_feed_id."""
    get_headers_per_file.clear()

    # pylint: disable=unused-argument
    def mock_get(url, headers, timeout, verify):
        """Mock requests.get."""
        assert timeout is not None
        assert verify is False
        assert headers is not None
        return MockResponse(
            json_data={'value': deepcopy(feeds_data)}, ok=True)

    monkeypatch.setattr('requests.get', mock_get)
    with TemporaryDirectory() as dirname:
        pat_file = dirname + '/pat.txt'
        with open(file=pat_file, mode='w', encoding='utf-8') as file:
            file.write('test_token')
        url_info = UrlInfo(instance='test.com', collection='col1',
                           pat_file=pat_file)
        with pytest.raises(RestException) as exc:
            _ = get_feed_id(url_info=url_info,
                            lookup_name=deepcopy(lookup_name))
        assert 'Feed ID not found' in str(exc.value)
        out, err = capsys.readouterr()
        assert '' == out
        assert 'Feed ID not found' in err


@pytest.mark.parametrize('meta,key,expected',
                         [({'name': 'test', 'version': '1.0'},
                           'name', 'test'),
                          ({'name': 'test', 'version': '1.0'},
                           'version', '1.0'),
                          ({'Name': 'pkg', 'Version': '2.0'},
                           'Name', 'pkg')])
def test_get_from_meta_ok1(capsys, meta, key, expected):
    """Test OK cases of get_from_meta."""
    ret = get_from_meta(meta=deepcopy(meta), key=deepcopy(key))
    assert ret == expected
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('meta,key',
                         [({'name': 'test'}, 'version'),
                          ({'Name': 'pkg'}, 'Version'),
                          ({}, 'name')])
def test_get_from_meta_missing_key(capsys, meta, key):
    """Test get_from_meta with missing key."""
    ret = get_from_meta(meta=deepcopy(meta), key=deepcopy(key))
    assert ret == ''
    out, err = capsys.readouterr()
    assert '' == out
    assert f'no "{key}" in:' in err


@pytest.mark.parametrize(
    'ver,expected',
    [({'protocolMetadata': {
        'data': {'Name': 'test', 'Version': '1.0.0',
                 'MetadataVersion': '2.1'}}},
      ('test', '1.0.0', '2.1')),
     ({'protocolMetadata': {
         'data': {'Name': 'pkg', 'Version': '2.0.0',
                  'MetadataVersion': '2.4'}}},
      ('pkg', '2.0.0', '2.4'))])
def test_parse_meta_ok1(capsys, ver, expected):
    """Test OK cases of parse_meta."""
    ret = parse_meta(ver=deepcopy(ver))
    assert ret == expected
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('ver',
                         [({'no_protocolMetadata': {}}),
                          ({'protocolMetadata': {}}),
                          ({'protocolMetadata': {'no_data': {}}})])
def test_parse_meta_nok1(capsys, ver):
    """Test not OK cases of parse_meta."""
    ret = parse_meta(ver=deepcopy(ver))
    assert ret == ('', '', '')
    out, err = capsys.readouterr()
    assert '' == out
    # May have error messages depending on the case
    if 'protocolMetadata' in ver and 'data' not in ver['protocolMetadata']:
        assert 'No data in meta' in err


@pytest.mark.parametrize(
    'pfile,name,version,metaversion,include_types,expected',
    [({'name': 'test.whl',
       'protocolMetadata': {
           'data': {'FileType': 'wheel'}}},
      'test', '1.0.0', '2.1', ['wheel'],
      SinglePkgInfo(name='test', version='1.0.0',
                    metadata_version='2.1',
                    package_type='wheel', file_name='test.whl')),
     ({'name': 'pkg.tar.gz',
       'protocolMetadata': {
           'data': {'FileType': 'sdist'}}},
      'pkg', '2.0.0', '2.4', ['sdist'],
      SinglePkgInfo(name='pkg', version='2.0.0',
                    metadata_version='2.4',
                    package_type='sdist', file_name='pkg.tar.gz')),
     ({'name': 'test.whl',
       'protocolMetadata': {
           'data': {'FileType': 'wheel'}}},
      'test', '1.0.0', '2.1', [],
      SinglePkgInfo(name='test', version='1.0.0',
                    metadata_version='2.1',
                    package_type='wheel', file_name='test.whl'))])
# pylint: disable=too-many-arguments,too-many-positional-arguments
def test_parse_fileinfo_ok1(capsys, pfile, name, version, metaversion,
                            include_types, expected):
    """Test OK cases of parse_fileinfo."""
    ret = parse_fileinfo(pfile=deepcopy(pfile), name=deepcopy(name),
                         version=deepcopy(version),
                         metaversion=deepcopy(metaversion),
                         include_types=deepcopy(include_types))
    assert ret == expected
    out, _ = capsys.readouterr()
    assert '' == out


@pytest.mark.parametrize(
    'pfile,name,version,metaversion,include_types',
    [({'name': 'test.whl',
       'protocolMetadata': {
           'data': {'FileType': 'wheel'}}},
      'test', '1.0.0', '2.1', ['sdist']),
     ({'name': 'test.tar.gz',
       'protocolMetadata': {
           'data': {'FileType': 'sdist'}}},
      'test', '1.0.0', '2.1', ['wheel']),
     ({'name': 'test.whl'},
      'test', '1.0.0', '2.1', ['wheel']),
     ({'name': 'test.whl',
       'protocolMetadata': {}},
      'test', '1.0.0', '2.1', ['wheel']),
     ({'name': 'test.whl',
       'protocolMetadata': {
           'data': {}}},
      'test', '1.0.0', '2.1', ['wheel'])])
# pylint: disable=too-many-arguments,too-many-positional-arguments
def test_parse_fileinfo_nok1(capsys, pfile, name, version, metaversion,
                             include_types):
    """Test not OK cases of parse_fileinfo."""
    ret = parse_fileinfo(pfile=deepcopy(pfile), name=deepcopy(name),
                         version=deepcopy(version),
                         metaversion=deepcopy(metaversion),
                         include_types=deepcopy(include_types))
    assert ret is None
    out, _ = capsys.readouterr()
    assert '' == out
    # May have error messages depending on the case


@pytest.mark.parametrize(
    'versions_data,include_types,expected_len',
    [([{'protocolMetadata': {
        'data': {'Name': 'test', 'Version': '1.0.0',
                 'MetadataVersion': '2.1'}},
        'files': [{'name': 'test.whl',
                   'protocolMetadata': {
                       'data': {'FileType': 'wheel'}}}]}],
      ['wheel'], 1),
     ([{'protocolMetadata': {
         'data': {'Name': 'test', 'Version': '1.0.0',
                  'MetadataVersion': '2.1'}},
        'files': [{'name': 'test.whl',
                   'protocolMetadata': {
                       'data': {'FileType': 'wheel'}}},
                  {'name': 'test.tar.gz',
                   'protocolMetadata': {
                       'data': {'FileType': 'sdist'}}}]}],
      [], 2),
     ([{'protocolMetadata': {
         'data': {'Name': 'test', 'Version': '1.0.0',
                  'MetadataVersion': '2.1'}},
        'files': [{'name': 'test.whl',
                   'protocolMetadata': {
                       'data': {'FileType': 'wheel'}}}]},
       {'protocolMetadata': {
           'data': {'Name': 'test', 'Version': '2.0.0',
                    'MetadataVersion': '2.1'}},
        'files': [{'name': 'test2.whl',
                   'protocolMetadata': {
                       'data': {'FileType': 'wheel'}}}]}],
      ['wheel'], 2)])
def test_get_pkg_versions_ok1(capsys, monkeypatch, versions_data,
                              include_types, expected_len):
    """Test OK cases of get_pkg_versions."""
    get_headers_per_file.clear()

    # pylint: disable=unused-argument
    def mock_get(url, headers, timeout, verify):
        """Mock requests.get."""
        assert timeout is not None
        assert verify is False
        assert headers is not None
        return MockResponse(
            json_data={'value': deepcopy(versions_data)}, ok=True)

    monkeypatch.setattr('requests.get', mock_get)
    with TemporaryDirectory() as dirname:
        pat_file = dirname + '/pat.txt'
        with open(file=pat_file, mode='w', encoding='utf-8') as file:
            file.write('test_token')
        ret = get_pkg_versions(url='http://test.com/pkg',
                               include_types=deepcopy(include_types),
                               pat_file=pat_file)
        assert len(ret) == expected_len
        out, _ = capsys.readouterr()
        assert '' == out


@pytest.mark.parametrize(
    'versions_data,include_types,expected_len',
    [([{'protocolMetadata': {
        'data': {'Name': '', 'Version': '',
                 'MetadataVersion': '2.1'}},
        'files': [{'name': 'test.whl',
                   'protocolMetadata': {
                       'data': {'FileType': 'wheel'}}}]}],
      ['wheel'], 0),
     ([{'protocolMetadata': {
         'data': {'Name': 'test', 'Version': '1.0.0',
                  'MetadataVersion': '2.1'}},
        'files': [{'name': 'test.whl',
                   'protocolMetadata': {
                       'data': {'FileType': 'wheel'}}}]},
       {'protocolMetadata': {
           'data': {'Name': '', 'Version': '',
                    'MetadataVersion': '2.1'}},
        'files': [{'name': 'test2.whl',
                   'protocolMetadata': {
                       'data': {'FileType': 'wheel'}}}]}],
      ['wheel'], 1),
     ([{}],
      ['wheel'], 0)])
def test_get_pkg_versions_empty_name_version(capsys, monkeypatch,
                                             versions_data,
                                             include_types, expected_len):
    """Test get_pkg_versions with empty name and version."""
    get_headers_per_file.clear()

    # pylint: disable=unused-argument
    def mock_get(url, headers, timeout, verify):
        """Mock requests.get."""
        assert timeout is not None
        assert verify is False
        assert headers is not None
        return MockResponse(
            json_data={'value': deepcopy(versions_data)}, ok=True)

    monkeypatch.setattr('requests.get', mock_get)
    with TemporaryDirectory() as dirname:
        pat_file = dirname + '/pat.txt'
        with open(file=pat_file, mode='w', encoding='utf-8') as file:
            file.write('test_token')
        ret = get_pkg_versions(url='http://test.com/pkg',
                               include_types=deepcopy(include_types),
                               pat_file=pat_file)
        assert len(ret) == expected_len
        out, _ = capsys.readouterr()
        assert '' == out


@pytest.mark.parametrize(
    'versions_data,include_types,expected_len,expected_err',
    [([{'protocolMetadata': {
        'data': {'Name': 'test', 'Version': '1.0.0',
                 'MetadataVersion': '2.1'}}}],
      ['wheel'], 0, 'No files in ver name=test'),
     ([{'protocolMetadata': {
         'data': {'Name': 'pkg1', 'Version': '2.0.0',
                  'MetadataVersion': '2.1'}},
        'files': [{'name': 'pkg1.whl',
                   'protocolMetadata': {
                       'data': {'FileType': 'wheel'}}}]},
       {'protocolMetadata': {
           'data': {'Name': 'pkg2', 'Version': '3.0.0',
                    'MetadataVersion': '2.1'}}}],
      ['wheel'], 1, 'No files in ver name=pkg2'),
     ([{'protocolMetadata': {
         'data': {'Name': 'mypackage', 'Version': '1.5.0',
                  'MetadataVersion': '2.4'}}}],
      [], 0, 'No files in ver name=mypackage')])
# pylint: disable=too-many-arguments,too-many-positional-arguments
def test_get_pkg_versions_no_files(capsys, monkeypatch, versions_data,
                                   include_types, expected_len,
                                   expected_err):
    """Test get_pkg_versions when files key is missing."""
    get_headers_per_file.clear()

    # pylint: disable=unused-argument
    def mock_get(url, headers, timeout, verify):
        """Mock requests.get."""
        assert timeout is not None
        assert verify is False
        assert headers is not None
        return MockResponse(
            json_data={'value': deepcopy(versions_data)}, ok=True)

    monkeypatch.setattr('requests.get', mock_get)
    with TemporaryDirectory() as dirname:
        pat_file = dirname + '/pat.txt'
        with open(file=pat_file, mode='w', encoding='utf-8') as file:
            file.write('test_token')
        ret = get_pkg_versions(url='http://test.com/pkg',
                               include_types=deepcopy(include_types),
                               pat_file=pat_file)
        assert len(ret) == expected_len
        out, err = capsys.readouterr()
        assert '' == out
        assert expected_err in err


@pytest.mark.parametrize(
    'packages_data,feeds_data,include_types,expected_len',
    [([{'url': 'http://test.com/pkg1',
        'normalizedName': 'test'}],
      [{'fullyQualifiedName': 'packages', 'id': 'feed-id'}],
      ['wheel'], 1),
     ([{'url': 'http://test.com/pkg1',
        'normalizedName': 'test1'},
       {'url': 'http://test.com/pkg2',
        'normalizedName': 'test2'}],
      [{'fullyQualifiedName': 'packages', 'id': 'feed-id'}],
      [], 2)])
# pylint: disable=too-many-arguments,too-many-positional-arguments
def test_get_pkgs_ok1(capsys, monkeypatch, packages_data, feeds_data,
                      include_types, expected_len):
    """Test OK cases of get_pkgs."""
    get_headers_per_file.clear()
    call_count = {'count': 0}

    # pylint: disable=unused-argument
    def mock_get(url, headers, timeout, verify):
        """Mock requests.get."""
        assert timeout is not None
        assert verify is False
        assert headers is not None
        call_count['count'] += 1
        if 'feeds' in url:
            return MockResponse(
                json_data={'value': deepcopy(feeds_data)}, ok=True)
        if 'packages' in url:
            return MockResponse(
                json_data={'value': deepcopy(packages_data)}, ok=True)
        if 'Versions' in url:
            return MockResponse(json_data={'value': []}, ok=True)
        return MockResponse(json_data={}, ok=True)

    monkeypatch.setattr('requests.get', mock_get)
    with TemporaryDirectory() as dirname:
        pat_file = dirname + '/pat.txt'
        with open(file=pat_file, mode='w', encoding='utf-8') as file:
            file.write('test_token')
        url_info = UrlInfo(instance='test.com', collection='col1',
                           pat_file=pat_file)
        ret = get_pkgs(url_info=url_info, project=None,
                       include_types=deepcopy(include_types))
        assert len(ret) == expected_len
        out, _ = capsys.readouterr()
        assert '' == out


@pytest.mark.parametrize(
    'packages_data,feeds_data,project,include_types',
    [([{'url': 'http://test.com/pkg1',
        'normalizedName': 'test'}],
      [{'fullyQualifiedName': 'packages', 'id': 'feed-id'}],
      'myproject', ['wheel']),
     ([{'url': 'http://test.com/pkg1',
        'normalizedName': 'test'}],
      [{'fullyQualifiedName': 'packages', 'id': 'feed-id'}],
      None, [])])
# pylint: disable=too-many-arguments,too-many-positional-arguments
# pylint: disable=too-many-locals
def test_get_pkgs_with_project(capsys, monkeypatch, packages_data,
                               feeds_data, project, include_types):
    """Test get_pkgs with project parameter."""
    get_headers_per_file.clear()
    urls_called = []

    # pylint: disable=unused-argument
    def mock_get(url, headers, timeout, verify):
        """Mock requests.get."""
        assert timeout is not None
        assert verify is False
        assert headers is not None
        urls_called.append(url)
        if 'feeds' in url:
            return MockResponse(
                json_data={'value': deepcopy(feeds_data)}, ok=True)
        if 'packages' in url:
            return MockResponse(
                json_data={'value': deepcopy(packages_data)}, ok=True)
        if 'Versions' in url:
            return MockResponse(json_data={'value': []}, ok=True)
        return MockResponse(json_data={}, ok=True)

    monkeypatch.setattr('requests.get', mock_get)
    with TemporaryDirectory() as dirname:
        pat_file = dirname + '/pat.txt'
        with open(file=pat_file, mode='w', encoding='utf-8') as file:
            file.write('test_token')
        url_info = UrlInfo(instance='test.com', collection='col1',
                           pat_file=pat_file)
        ret = get_pkgs(url_info=url_info, project=project,
                       include_types=deepcopy(include_types))
        assert ret is not None
        # Check if project was included in URL
        packages_url = [u for u in urls_called if 'packages' in u][0]
        if project:
            assert f'{project}/' in packages_url
        out, _ = capsys.readouterr()
        assert '' == out


# pylint: disable=too-many-locals
def test_list_ado_content_ok1(capsys, monkeypatch):
    """Test OK case of list_ado_content."""
    get_headers_per_file.clear()
    packages_data = [{'url': 'http://test.com/pkg1',
                      'normalizedName': 'test'}]
    feeds_data = [{'fullyQualifiedName': 'packages',
                   'id': 'feed-id'}]
    versions_data = [{
        'protocolMetadata': {
            'data': {'Name': 'test', 'Version': '1.0.0',
                     'MetadataVersion': '2.1'}},
        'files': [{'name': 'test.whl',
                   'protocolMetadata': {
                       'data': {'FileType': 'wheel'}}}]}]

    # pylint: disable=unused-argument
    def mock_get(url, headers, timeout, verify):
        """Mock requests.get."""
        assert timeout is not None
        assert verify is False
        assert headers is not None
        if 'feeds' in url:
            return MockResponse(
                json_data={'value': deepcopy(feeds_data)}, ok=True)
        if 'Versions' in url:
            return MockResponse(
                json_data={'value': deepcopy(versions_data)}, ok=True)
        if 'packages' in url:
            return MockResponse(
                json_data={'value': deepcopy(packages_data)}, ok=True)
        return MockResponse(json_data={}, ok=True)

    monkeypatch.setattr('requests.get', mock_get)
    with TemporaryDirectory() as dirname:
        pat_file = dirname + '/pat.txt'
        with open(file=pat_file, mode='w', encoding='utf-8') as file:
            file.write('test_token')
        output_file = dirname + '/output.csv'
        url_info = UrlInfo(instance='test.com', collection='col1',
                           pat_file=pat_file)
        ret = list_ado_content(file_name=output_file, url_info=url_info,
                               project=None, include_types=['wheel'])
        assert ret == 0
        with open(file=output_file, mode='r', encoding='utf-8',
                  newline='') as file:
            reader = csv.reader(file, dialect='unix')
            rows = list(reader)
        assert len(rows) == 2
        assert rows[0] == ['Name', 'Name of version', 'Version',
                           'Metadata version', 'package type',
                           'file name']
        out, err = capsys.readouterr()
        assert '' == out
        assert 'Output file name:' in err
        assert 'instance: test.com' in err
        assert 'collection: col1' in err


def test_rest_exception():
    """Test RestException can be created and raised."""
    exc = RestException('test error')
    assert str(exc) == 'test error'
    with pytest.raises(RestException) as exc_info:
        raise RestException('test message')
    assert 'test message' in str(exc_info.value)


def test_single_pkg_info():
    """Test SinglePkgInfo named tuple."""
    pkg = SinglePkgInfo(name='test', version='1.0.0',
                        metadata_version='2.1',
                        package_type='wheel',
                        file_name='test-1.0.0.whl')
    assert pkg.name == 'test'
    assert pkg.version == '1.0.0'
    assert pkg.metadata_version == '2.1'
    assert pkg.package_type == 'wheel'
    assert pkg.file_name == 'test-1.0.0.whl'


def test_pkg_info():
    """Test PkgInfo named tuple."""
    single = SinglePkgInfo(name='test', version='1.0.0',
                           metadata_version='2.1',
                           package_type='wheel',
                           file_name='test-1.0.0.whl')
    pkg = PkgInfo(name='test', versions=[single])
    assert pkg.name == 'test'
    assert len(pkg.versions) == 1
    assert pkg.versions[0] == single


def test_url_info():
    """Test UrlInfo named tuple."""
    url_info = UrlInfo(instance='test.com', collection='col1',
                       pat_file='/path/to/pat.txt')
    assert url_info.instance == 'test.com'
    assert url_info.collection == 'col1'
    assert url_info.pat_file == '/path/to/pat.txt'
