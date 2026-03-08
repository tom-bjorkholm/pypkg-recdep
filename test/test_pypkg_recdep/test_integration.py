#! /usr/local/bin/python3
"""Integration tests for complete program flow."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

from copy import deepcopy
from tempfile import TemporaryDirectory
import csv
import os
import re
from typing import Optional
import pytest
from test_list_ado_content import MockResponse
from test_internal_serv_listing import MockListClient, create_test_list_data
from test_find_pypi_deps2 import MockClient1, MockSpecPage, MockSpecMeta, \
    LookupWhat, create_test_pkg_spec
from pypkg_recdep.pkg_recdep_cmd import pypkg_recdep_cmd
from pypkg_recdep.list_ado_content import PkgInfo, SinglePkgInfo


# Section with tests of printdeps subcommand


@pytest.mark.parametrize('args,expected_content',
                         [(['printdeps', '--package', 'test-pkg',
                            '--output', 'output.md'],
                           [r'# Package dependency information for test-pkg',
                            r'test-pkg',
                            r'packaging',
                            r'\(End of document\.\)']),
                          (['printdeps', '-p', 'mypkg', '-m', '2.4',
                            '-y', '3.13', '-o', 'deps.md'],
                           [r'# Package dependency information for mypkg',
                            r'mypkg',
                            r'\(End of document\.\)'])])
def test_printdeps_integration(
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str], args: list[str],
        expected_content: list[str]) -> None:
    """Test printdeps subcommand end-to-end."""
    # Create mock spec for PyPISimple
    spec = create_test_pkg_spec()
    # Add mypkg for the second test case
    spec.append(
        MockSpecPage(
            name='mypkg',
            base='elt',
            metas=[
                MockSpecMeta(meta=True, version='1.0.0',
                             metaversion='2.4',
                             reqs=[],
                             py_req='>=3.10')
            ]
        )
    )

    def mock_pypisimple() -> MockClient1:
        """Return MockClient1."""
        return MockClient1(spec=deepcopy(spec),
                           lookup=LookupWhat.LOOKUP_NAME)

    monkeypatch.setattr('pypkg_recdep.find_pypi_deps.PyPISimple',
                        mock_pypisimple)

    with TemporaryDirectory() as temp_dir:
        # Update output file path
        output_idx = (args.index('--output') + 1
                      if '--output' in args
                      else args.index('-o') + 1)
        output_file = os.path.join(temp_dir, args[output_idx])
        args[output_idx] = output_file

        # Run command
        ret = pypkg_recdep_cmd(arguments=args)
        assert ret == 0

        # Verify output file exists and has expected content
        assert os.path.exists(output_file), \
            f"Output file {output_file} not created"
        with open(output_file, 'r', encoding='utf-8') as file:
            content = file.read()
        for pattern in expected_content:
            assert re.search(pattern, content), \
                f"Pattern {pattern} not found in output"

    out, err = capsys.readouterr()
    assert '' == out
    # Allow stderr output from list_ado_content
    assert 'Output file name:' in err or '' == err


# Section with tests of listado subcommand


@pytest.mark.parametrize('args,expected_rows',
                         [(['listado', '--output', 'ado.csv'],
                           [['Name', 'Name of version', 'Version',
                             'Metadata version', 'package type',
                             'file name']]),
                          (['listado', '-s', 'myserver', '-c', 'mycoll',
                            '-o', 'output.csv'],
                           [['Name', 'Name of version', 'Version',
                             'Metadata version', 'package type',
                             'file name']])])
# pylint: disable=too-many-locals
def test_listado_integration(
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str], args: list[str],
        expected_rows: list[list[str]]) -> None:
    """Test listado subcommand end-to-end."""
    # Create mock response for requests.get
    json_data = {
        'value': [
            {
                'id': 'feed-id-123',
                'name': 'Python'
            }
        ]
    }
    mock_response = MockResponse(json_data=json_data)

    def mock_get(url: object, headers: Optional[dict[str, str]] = None,
                 auth: object = None,
                 timeout: Optional[float] = None) -> MockResponse:
        """Mock requests.get."""
        _ = url, headers, auth, timeout
        return mock_response

    monkeypatch.setattr('requests.get', mock_get)
    monkeypatch.setattr('requests.Session.get', mock_get)

    # Mock get_from_rest to return package data
    def mock_get_from_rest(url: object, headers: object, auth: object,
                           timeout: object) -> dict[str, list[object]]:
        """Mock get_from_rest."""
        _ = url, headers, auth, timeout
        return {
            'value': [
                {
                    'name': 'testpkg',
                    'versions': [
                        {
                            'version': '1.0.0',
                            'files': [
                                {
                                    'name': 'testpkg-1.0.0.whl',
                                    'protocolMetadata': {
                                        'data': {
                                            'packageType': 'wheel'
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }

    monkeypatch.setattr('pypkg_recdep.list_ado_content.get_from_rest',
                        mock_get_from_rest)

    # Mock get_feed_id
    def mock_get_feed_id(instance: object, collection: object,
                         pat_file: object) -> str:
        """Mock get_feed_id."""
        _ = instance, collection, pat_file
        return 'feed-id-123'

    monkeypatch.setattr('pypkg_recdep.list_ado_content.get_feed_id',
                        mock_get_feed_id)

    # Mock get_pkgs
    def mock_get_pkgs(url_info: object, project: object,
                      include_types: object) -> list[PkgInfo]:
        """Mock get_pkgs."""
        _ = url_info, project, include_types
        return [
            PkgInfo(
                name='testpkg',
                versions=[
                    SinglePkgInfo(
                        name='testpkg',
                        version='1.0.0',
                        metadata_version='2.1',
                        package_type='wheel',
                        file_name='testpkg-1.0.0.whl')
                ]
            )
        ]

    monkeypatch.setattr('pypkg_recdep.list_ado_content.get_pkgs',
                        mock_get_pkgs)

    with TemporaryDirectory() as temp_dir:
        # Update output file path
        output_idx = (args.index('--output') + 1
                      if '--output' in args
                      else args.index('-o') + 1)
        output_file = os.path.join(temp_dir, args[output_idx])
        args[output_idx] = output_file

        # Run command
        ret = pypkg_recdep_cmd(arguments=args)
        assert ret == 0

        # Verify output file exists and has expected content
        assert os.path.exists(output_file), \
            f"Output file {output_file} not created"
        with open(output_file, 'r', encoding='utf-8', newline='') as file:
            reader = csv.reader(file, dialect='unix')
            rows = list(reader)
        assert len(rows) > 0, "Output file is empty"
        assert rows[0] == expected_rows[0], \
            f"Header row mismatch: {rows[0]} != {expected_rows[0]}"

    out, err = capsys.readouterr()
    assert '' == out
    # Allow stderr output from list_ado_content
    assert 'Output file name:' in err or '' == err


# Section with tests of listinternal subcommand


@pytest.mark.parametrize('args,expected_rows',
                         [(['listinternal', '--output', 'internal.csv'],
                           [['Name', 'Version', 'Metadata Version',
                             'Formats']]),
                          (['listinternal', '-u', 'http://test.com',
                            '-o', 'output.csv', '-n', '5'],
                           [['Name', 'Version', 'Metadata Version',
                             'Formats']])])
def test_listinternal_integration(
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str], args: list[str],
        expected_rows: list[list[str]]) -> None:
    """Test listinternal subcommand end-to-end."""
    # Create test data for MockListClient
    test_data = create_test_list_data(
        project_name='testpkg',
        packages=[
            ('testpkg', '1.0.0', '2.1', 'wheel')
        ]
    )

    def mock_pypisimple(endpoint: object, auth: object = None) -> \
            MockListClient:
        """Return MockListClient."""
        _ = endpoint, auth
        return MockListClient(data=deepcopy(test_data))

    monkeypatch.setattr('pypkg_recdep.internal_server_listing.PyPISimple',
                        mock_pypisimple)

    with TemporaryDirectory() as temp_dir:
        # Update output file path
        output_idx = (args.index('--output') + 1
                      if '--output' in args
                      else args.index('-o') + 1)
        output_file = os.path.join(temp_dir, args[output_idx])
        args[output_idx] = output_file

        # Run command
        ret = pypkg_recdep_cmd(arguments=args)
        assert ret == 0

        # Verify output file exists and has expected content
        assert os.path.exists(output_file), \
            f"Output file {output_file} not created"
        with open(output_file, 'r', encoding='utf-8', newline='') as file:
            reader = csv.reader(file, dialect='unix')
            rows = list(reader)
        assert len(rows) > 0, "Output file is empty"
        assert rows[0] == expected_rows[0], \
            f"Header row mismatch: {rows[0]} != {expected_rows[0]}"

    out, err = capsys.readouterr()
    assert '' == out
    # Allow stderr output from list_in_internal_server
    assert 'Found' in err or '' == err
