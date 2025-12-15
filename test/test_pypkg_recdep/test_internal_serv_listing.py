#! /usr/local/bin/python3
"""Test listing of content in internal PyPI."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

from copy import deepcopy
from typing import Optional
import re
# import pytest
from packaging.version import Version
from pypi_simple import IndexPage, ProjectPage
from get_example_pypi_list_data import load_example_pypi_list_data, \
    MockListData
from pypkg_recdep.pkg_info import PkgKey
# from pypkg_recdep.internal_server_listing import NoAuth, TokenAuth


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
