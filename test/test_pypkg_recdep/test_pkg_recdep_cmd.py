#! /usr/local/bin/python3
"""Test command line parsing of pypkg_recdep."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

from copy import deepcopy
from typing import Optional
import os
import re
from tempfile import TemporaryDirectory
import pytest
from pypkg_recdep.pkg_recdep_cmd import pypkg_recdep_cmd
from pypkg_recdep.list_ado_content import UrlInfo
from pypkg_recdep.exclude import ExcludeInfo


# Section with tests of help text generation


@pytest.mark.parametrize('args,expected_patterns',
                         [(['--help'],
                           [r'usage:.*pypkg_recdep',
                            r'List recursive dependencies of package',
                            r'More detailed help is available',
                            r'positional arguments:',
                            r'printdeps',
                            r'listado',
                            r'listinternal']),
                          (['printdeps', '--help'],
                           [r'usage:.*pypkg_recdep printdeps',
                            r'Print all recursive dependencies',
                            r'Useful to figure out which packages',
                            r'-p.*--package',
                            r'Package or application to list',
                            r'-m.*--metadatamax',
                            r'Highest allowed metadata version',
                            r'-y.*--pythonversion',
                            r'Works on python version',
                            r'-e.*--excludecsv',
                            r'File name of CSV file',
                            r'-t.*--excludetext',
                            r'Text to include in report',
                            r'-o.*--output',
                            r'Name of output markdown file',
                            r'-l.*--listpurls',
                            r'Name of file with list of packages']),
                          (['listado', '--help'],
                           [r'usage:.*pypkg_recdep listado',
                            r'List python packages in Azure Dev Ops',
                            r'Useful when having internal ADO',
                            r'-s.*--instance',
                            r'Instance or server name',
                            r'-c.*--collection',
                            r'Collection',
                            r'-p.*--project',
                            r'Project',
                            r'-i.*--include-types',
                            r'Comma separated list of package types',
                            r'-a.*--patfile',
                            r'File name of file with personal access token',
                            r'-o.*--output',
                            r'Name of output CSV file']),
                          (['listinternal', '--help'],
                           [r'usage:.*pypkg_recdep listinternal',
                            r'List python packages in internal PyPI',
                            r'Useful when having internal PyPI',
                            r'(Never run this towards pypi\.org|pypi\.org)',
                            r'-u.*--url',
                            r'Base URL to internal PyPI server',
                            r'-o.*--output',
                            r'Name of output CSV file',
                            r'-n.*--limitnumber',
                            r'Limit output to this number',
                            r'-a.*--patfile',
                            r'File name of file with personal access token'
                            ])])
def test_help_text(capsys, args, expected_patterns):
    """Test help text generation for all commands."""
    with pytest.raises(SystemExit) as exc_info:
        pypkg_recdep_cmd(arguments=deepcopy(args))
    assert exc_info.value.code == 0
    out, err = capsys.readouterr()
    help_text = out + err
    for pattern in expected_patterns:
        assert re.search(pattern, help_text, re.IGNORECASE), \
            f"Pattern '{pattern}' not found in help text"


# Section with tests of error messages for incorrect command lines


@pytest.mark.parametrize('args,expected_error',
                         [([],
                           r'error:.*(subparser_name|arguments).*required'),
                          (['invalid'],
                           r'error:.*invalid choice.*invalid'),
                          (['printdeps'],
                           r'error:.*(-p|--package|arguments).*required'),
                          (['printdeps', '--package'],
                           r'error:.*--package.*expected.*argument'),
                          (['listado', '--instance'],
                           r'error:.*--instance.*expected.*argument'),
                          (['listinternal', '--url'],
                           r'error:.*--url.*expected.*argument')])
def test_error_messages(capsys, args, expected_error):
    """Test error messages for incorrect command lines."""
    with pytest.raises(SystemExit) as exc_info:
        pypkg_recdep_cmd(arguments=deepcopy(args))
    assert exc_info.value.code != 0
    out, err = capsys.readouterr()
    error_text = out + err
    assert re.search(expected_error, error_text, re.IGNORECASE), \
        f"Expected error pattern '{expected_error}' not found"


# Section with tests of correct command lines


@pytest.mark.parametrize('args,expected_calls',
                         [(['printdeps', '--package', 'mypkg',
                            '--output', 'out.md'],
                           {'resolve_all_dependencies': {
                               'root_package': 'mypkg',
                               'python_version': 'check_default',
                               'max_metadata_version': 'check_default'},
                            'print_deps': {
                               'outfilename': 'out.md',
                               'purls': None,
                               'exclude_txt': 'no exclues',
                               'exclude_csv': None}}),
                          (['printdeps', '-p', 'testpkg', '-m', '2.1',
                            '-y', '3.12', '-o', 'test.md', '-l', 'purls.txt',
                            '-e', 'TEMP_EXCL_CSV', '-t', 'excluded text'],
                           {'resolve_all_dependencies': {
                               'root_package': 'testpkg',
                               'python_version': '3.12',
                               'max_metadata_version': '2.1'},
                            'print_deps': {
                               'outfilename': 'test.md',
                               'purls': 'purls.txt',
                               'exclude_txt': 'excluded text',
                               'exclude_csv': 'TEMP_EXCL_CSV'}}),
                          (['listado', '--output', 'ado.csv'],
                           {'list_ado_content': {
                               'file_name': 'ado.csv',
                               'url_info_instance': 'check_default',
                               'url_info_collection': 'check_default',
                               'url_info_pat_file': None,
                               'project': None,
                               'include_types': 'check_default'}}),
                          (['listado', '-s', 'myserver', '-c', 'mycoll',
                            '-p', 'myproj', '-i', 'wheel,sdist',
                            '-a', 'pat.txt', '-o', 'output.csv'],
                           {'list_ado_content': {
                               'file_name': 'output.csv',
                               'url_info': UrlInfo(
                                   instance='myserver',
                                   collection='mycoll',
                                   pat_file='pat.txt'),
                               'project': 'myproj',
                               'include_types': ['wheel', 'sdist']}}),
                          (['listado', '-p', 'None'],
                           {'list_ado_content': {
                               'project': None}}),
                          (['listinternal', '--output', 'internal.csv'],
                           {'list_in_internal_server': {
                               'server_url': 'check_default',
                               'pat_file': None,
                               'output_file': 'internal.csv',
                               'limit': None}}),
                          (['listinternal', '-u', 'http://test.com',
                            '-a', 'token.txt', '-o', 'out.csv', '-n', '10'],
                           {'list_in_internal_server': {
                               'server_url': 'http://test.com',
                               'pat_file': 'token.txt',
                               'output_file': 'out.csv',
                               'limit': 10}})])
# pylint: disable=too-many-locals,too-many-branches,too-many-statements
def test_correct_command_lines(capsys, monkeypatch, args, expected_calls):
    """Test correct command lines with mocked functions."""
    # Create temporary CSV file if needed
    if 'TEMP_EXCL_CSV' in str(args):
        with TemporaryDirectory() as temp_dir:
            temp_csv_path = os.path.join(temp_dir, 'excl.csv')
            with open(temp_csv_path, 'w', encoding='utf-8') as temp_file:
                temp_file.write('Name,Version\n')
                temp_file.write('testpkg,1.0.0\n')
            # Verify file exists
            assert os.path.exists(temp_csv_path), \
                f"Temp CSV file not created: {temp_csv_path}"
            # Replace TEMP_EXCL_CSV with actual file name
            args = [arg.replace('TEMP_EXCL_CSV', temp_csv_path)
                    if isinstance(arg, str) else arg for arg in args]
            # Update expected_calls
            if 'print_deps' in expected_calls:
                if 'exclude_csv' in expected_calls['print_deps']:
                    expected_calls['print_deps']['exclude_csv'] = \
                        temp_csv_path

            # Track function calls
            call_log: dict[str, list[dict]] = {}

            def mock_resolve_all_dependencies(root_package: str,
                                              python_version: str,
                                              max_metadata_version:
                                              Optional[str] = None):
                """Mock resolve_all_dependencies."""
                call_log.setdefault('resolve_all_dependencies', []).append({
                    'root_package': root_package,
                    'python_version': python_version,
                    'max_metadata_version': max_metadata_version})
                return {}

            def mock_print_deps(deps, outfilename: str, purls: Optional[str],
                                exclude: ExcludeInfo):
                """Mock print_deps."""
                # Suppress unused argument warning
                _ = deps
                call_log.setdefault('print_deps', []).append({
                    'outfilename': outfilename,
                    'purls': purls,
                    'exclude_txt': exclude.txt,
                    'exclude_csv': exclude.csv_filename
                    if exclude.csv_filename != 'None' else None})
                return 0

            def mock_list_ado_content(file_name: str, url_info: UrlInfo,
                                      project: Optional[str],
                                      include_types: list[str]):
                """Mock list_ado_content."""
                call_log.setdefault('list_ado_content', []).append({
                    'file_name': file_name,
                    'url_info': url_info,
                    'url_info_instance': url_info.instance,
                    'url_info_collection': url_info.collection,
                    'url_info_pat_file': url_info.pat_file,
                    'project': project,
                    'include_types': include_types})
                return 0

            def mock_list_in_internal_server(server_url: str, pat_file: str,
                                             output_file: str,
                                             limit: Optional[int]):
                """Mock list_in_internal_server."""
                call_log.setdefault('list_in_internal_server', []).append({
                    'server_url': server_url,
                    'pat_file': pat_file,
                    'output_file': output_file,
                    'limit': limit})

            # Patch functions
            monkeypatch.setattr(
                'pypkg_recdep.print_deps.resolve_all_dependencies',
                mock_resolve_all_dependencies)
            monkeypatch.setattr(
                'pypkg_recdep.print_deps.print_deps',
                mock_print_deps)
            monkeypatch.setattr(
                'pypkg_recdep.pkg_recdep_cmd.list_ado_content',
                mock_list_ado_content)
            monkeypatch.setattr(
                'pypkg_recdep.pkg_recdep_cmd.list_in_internal_server',
                mock_list_in_internal_server)

            # Verify file still exists before running command
            assert os.path.exists(temp_csv_path), \
                f"Temp CSV file missing before command: {temp_csv_path}"
            # Run command (don't deepcopy args to preserve temp_csv_path)
            ret = pypkg_recdep_cmd(arguments=args)
            assert ret == 0

            # Verify calls
            for func_name, expected_call in expected_calls.items():
                assert func_name in call_log, \
                    f"Function {func_name} was not called"
                calls = call_log[func_name]
                assert len(calls) == 1, \
                    f"Function {func_name} called {len(calls)} times, " \
                    f"expected 1"
                actual_call = calls[0]
                for key, expected_value in expected_call.items():
                    if key == 'url_info':
                        assert isinstance(actual_call[key], UrlInfo)
                        url_info = actual_call[key]
                        if expected_value.instance is not None:
                            assert url_info.instance == expected_value.instance
                        if expected_value.collection is not None:
                            assert url_info.collection == \
                                expected_value.collection
                        if expected_value.pat_file is not None:
                            assert url_info.pat_file == \
                                expected_value.pat_file
                    elif key == 'url_info_instance':
                        assert isinstance(actual_call['url_info'], UrlInfo)
                        url_info = actual_call['url_info']
                        if expected_value == 'check_default':
                            assert url_info.instance is not None
                        else:
                            assert url_info.instance == expected_value
                    elif key == 'url_info_collection':
                        assert isinstance(actual_call['url_info'], UrlInfo)
                        url_info = actual_call['url_info']
                        if expected_value == 'check_default':
                            assert url_info.collection is not None
                        else:
                            assert url_info.collection == expected_value
                    elif key == 'url_info_pat_file':
                        assert isinstance(actual_call['url_info'], UrlInfo)
                        url_info = actual_call['url_info']
                        assert url_info.pat_file == expected_value
                    elif key == 'exclude_txt':
                        assert actual_call[key] == expected_value, \
                            f"For {func_name}.{key}: expected " \
                            f"{expected_value}, got {actual_call[key]}"
                    elif key == 'exclude_csv':
                        assert actual_call[key] == expected_value, \
                            f"For {func_name}.{key}: expected " \
                            f"{expected_value}, got {actual_call[key]}"
                    elif key == 'include_types':
                        if expected_value == 'check_default':
                            assert actual_call[key] is not None
                        elif expected_value is not None:
                            assert actual_call[key] == expected_value
                    elif expected_value == 'check_default':
                        assert actual_call[key] is not None, \
                            f"For {func_name}.{key}: expected non-None " \
                            f"value, got {actual_call[key]}"
                    else:
                        if expected_value is not None:
                            assert actual_call[key] == expected_value, \
                                f"For {func_name}.{key}: expected " \
                                f"{expected_value}, got {actual_call[key]}"

            out, err = capsys.readouterr()
            assert '' == out
            assert '' == err
    else:
        # Track function calls
        call_log: dict[str, list[dict]] = {}

        def mock_resolve_all_dependencies(root_package: str,
                                          python_version: str,
                                          max_metadata_version:
                                          Optional[str] = None):
            """Mock resolve_all_dependencies."""
            call_log.setdefault('resolve_all_dependencies', []).append({
                'root_package': root_package,
                'python_version': python_version,
                'max_metadata_version': max_metadata_version})
            return {}

        def mock_print_deps(deps, outfilename: str, purls: Optional[str],
                            exclude: ExcludeInfo):
            """Mock print_deps."""
            # Suppress unused argument warning
            _ = deps
            call_log.setdefault('print_deps', []).append({
                'outfilename': outfilename,
                'purls': purls,
                'exclude_txt': exclude.txt,
                'exclude_csv': exclude.csv_filename
                if exclude.csv_filename != 'None' else None})
            return 0

        def mock_list_ado_content(file_name: str, url_info: UrlInfo,
                                  project: Optional[str],
                                  include_types: list[str]):
            """Mock list_ado_content."""
            call_log.setdefault('list_ado_content', []).append({
                'file_name': file_name,
                'url_info': url_info,
                'url_info_instance': url_info.instance,
                'url_info_collection': url_info.collection,
                'url_info_pat_file': url_info.pat_file,
                'project': project,
                'include_types': include_types})
            return 0

        def mock_list_in_internal_server(server_url: str, pat_file: str,
                                         output_file: str,
                                         limit: Optional[int]):
            """Mock list_in_internal_server."""
            call_log.setdefault('list_in_internal_server', []).append({
                'server_url': server_url,
                'pat_file': pat_file,
                'output_file': output_file,
                'limit': limit})

        # Patch functions
        monkeypatch.setattr(
            'pypkg_recdep.print_deps.resolve_all_dependencies',
            mock_resolve_all_dependencies)
        monkeypatch.setattr(
            'pypkg_recdep.print_deps.print_deps',
            mock_print_deps)
        monkeypatch.setattr(
            'pypkg_recdep.pkg_recdep_cmd.list_ado_content',
            mock_list_ado_content)
        monkeypatch.setattr(
            'pypkg_recdep.pkg_recdep_cmd.list_in_internal_server',
            mock_list_in_internal_server)

        # Run command
        ret = pypkg_recdep_cmd(arguments=args)
        assert ret == 0

        # Verify calls
        for func_name, expected_call in expected_calls.items():
            assert func_name in call_log, \
                f"Function {func_name} was not called"
            calls = call_log[func_name]
            assert len(calls) == 1, \
                f"Function {func_name} called {len(calls)} times, " \
                f"expected 1"
            actual_call = calls[0]
            for key, expected_value in expected_call.items():
                if key == 'url_info':
                    assert isinstance(actual_call[key], UrlInfo)
                    url_info = actual_call[key]
                    if expected_value.instance is not None:
                        assert url_info.instance == expected_value.instance
                    if expected_value.collection is not None:
                        assert url_info.collection == \
                            expected_value.collection
                    if expected_value.pat_file is not None:
                        assert url_info.pat_file == \
                            expected_value.pat_file
                elif key == 'url_info_instance':
                    assert isinstance(actual_call['url_info'], UrlInfo)
                    url_info = actual_call['url_info']
                    if expected_value == 'check_default':
                        assert url_info.instance is not None
                    else:
                        assert url_info.instance == expected_value
                elif key == 'url_info_collection':
                    assert isinstance(actual_call['url_info'], UrlInfo)
                    url_info = actual_call['url_info']
                    if expected_value == 'check_default':
                        assert url_info.collection is not None
                    else:
                        assert url_info.collection == expected_value
                elif key == 'url_info_pat_file':
                    assert isinstance(actual_call['url_info'], UrlInfo)
                    url_info = actual_call['url_info']
                    assert url_info.pat_file == expected_value
                elif key == 'exclude_txt':
                    assert actual_call[key] == expected_value, \
                        f"For {func_name}.{key}: expected " \
                        f"{expected_value}, got {actual_call[key]}"
                elif key == 'exclude_csv':
                    assert actual_call[key] == expected_value, \
                        f"For {func_name}.{key}: expected " \
                        f"{expected_value}, got {actual_call[key]}"
                elif key == 'include_types':
                    if expected_value == 'check_default':
                        assert actual_call[key] is not None
                    elif expected_value is not None:
                        assert actual_call[key] == expected_value
                elif expected_value == 'check_default':
                    assert actual_call[key] is not None, \
                        f"For {func_name}.{key}: expected non-None " \
                        f"value, got {actual_call[key]}"
                else:
                    if expected_value is not None:
                        assert actual_call[key] == expected_value, \
                            f"For {func_name}.{key}: expected " \
                            f"{expected_value}, got {actual_call[key]}"

        out, err = capsys.readouterr()
        assert '' == out
        assert '' == err
