#! /usr/local/bin/python3
"""Get and list python package content of internal PyPI server."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

import sys
import csv
from typing import Optional
import requests
from requests.auth import AuthBase
from pypi_simple import PyPISimple, DistributionPackage, NoMetadataError, \
    NoDigestsError, DigestMismatchError
from packaging.metadata import parse_email


class NoAuth(AuthBase):  # pylint: disable=too-few-public-methods
    """No authentication."""

    def __call__(self,
                 r: requests.PreparedRequest) -> requests.PreparedRequest:
        """Attach no authorization."""
        return r


class TokenAuth(AuthBase):  # pylint: disable=too-few-public-methods
    """Custom authentication class for a Personal Access Token (PAT)."""

    def __init__(self, token: str) -> None:
        """Create the TokenAuth object with the given token.

        @param token The token string to initialize with.
        """
        self.token = token

    def __call__(self,
                 r: requests.PreparedRequest) -> requests.PreparedRequest:
        """Attach the Authorization header with the bearer token.

        @param r  The prepared HTTP request.
        @return   The modified request with the Authorization header.
        """
        r.headers['Authorization'] = f'Bearer {self.token}'
        return r


def read_token_from_file(token_file: str) -> str:
    """Read the personal access token from a file.

    @param token_file  Path to the file containing the token.
    @return  The token as a string.
    """
    with open(token_file, 'r', encoding='utf-8') as file:
        return file.read().strip()


def get_auth(pat_file: str) -> NoAuth | TokenAuth:
    """Get authentication token based on file.

    @param pat_file  File name of Personal Access Token.
    """
    if pat_file:
        token = read_token_from_file(pat_file)
        return TokenAuth(token)
    return NoAuth()


def get_meta(client: PyPISimple, pkg: DistributionPackage) -> str:
    """Get metadata version for package.

    @param client   The PyPISimple client to use for queries.
    @param pkg      The package to get metadata for
    """
    if not pkg.has_metadata:
        return 'unknown'
    try:
        metadata = client.get_package_metadata(pkg=pkg, timeout=30.0)
        raw, _ = parse_email(metadata)
        if 'metadata_version' not in raw:
            return 'unknown'
        return raw['metadata_version']
    except (NoMetadataError, NoDigestsError, DigestMismatchError,
            requests.HTTPError, KeyError, ValueError) as exc:
        # Could not get_package_metadata()
        print(f'Failed to get metadata version for {pkg.project}: {str(exc)}',
              file=sys.stderr)
    return 'unknown'


def store_pkg(proj_pkgs: dict[str, dict[str, dict[str, str]]],
              name: Optional[str], ver: Optional[str],
              meta: str, ptype: Optional[str]) -> None:
    """Store data about package in proj_pkgs.

    @param proj_pkgs The collected information add information to.
    @param name The name of the package to add to collected information.
    @param ver The version or the package to add to collected information.
    @param meta The metadata version of the package.
    @param ptype The type of the package.
    """
    if name is None or ver is None:
        return
    assert name is not None
    assert ver is not None
    if ptype is None:
        ptype = 'unknown'
    assert ptype is not None
    if name not in proj_pkgs:
        proj_pkgs[name] = {ver: {'meta': meta, 'ptype': ptype}}
        return
    if ver not in proj_pkgs[name]:
        proj_pkgs[name][ver] = {'meta': meta, 'ptype': ptype}
        return
    if proj_pkgs[name][ver]['meta'] == 'unknown':
        proj_pkgs[name][ver]['meta'] = meta
    if ptype not in proj_pkgs[name][ver]['ptype']:
        proj_pkgs[name][ver]['ptype'] += ' + ' + ptype


def list_for_projects(client: PyPISimple, projects: list[str],
                      output_file: str) -> None:
    """List all releases of projects and write them to CSV.

    @param client      The PyPISimple client to use for queries.
    @param projects    The list of projects to list data for.
    @param output_file The name of the CSV file to create.
    """
    with open(output_file, 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file, dialect='unix')
        writer.writerow(['Name', 'Version', 'Metadata Version', 'Formats'])
        for proj in projects:
            req_page = client.get_project_page(project=proj, timeout=30.0)
            proj_pkgs: dict[str, dict[str, dict[str, str]]] = {}
            for pkg in req_page.packages:
                meta = get_meta(client=client, pkg=pkg)
                store_pkg(proj_pkgs=proj_pkgs, name=pkg.project,
                          ver=pkg.version, meta=meta, ptype=pkg.package_type)
            for name, pdata in proj_pkgs.items():
                for ver, vdata in pdata.items():
                    writer.writerow([name, ver, vdata['meta'],
                                     vdata['ptype']])


def list_in_internal_server(server_url: str, pat_file: str, output_file: str,
                            limit: Optional[int]) -> None:
    """List all releases on an internal PyPI server and write them to a CSV.

    @param server_url  The base URL of the internal PyPI server.
    @param pat_file    Path to the file holding the Personal Access Token.
    @param output_file Path to the output CSV file.
    @param limit       The maximum number of packages to list.
    """
    auth = get_auth(pat_file=pat_file)
    with PyPISimple(endpoint=server_url.rstrip('/') + '/simple',
                    auth=auth) as client:
        idxpage = client.get_index_page(timeout=30.0)
        projects = idxpage.projects
        if limit:
            print(f'Found {len(projects)} packages, ' +
                  f'limiting output to {limit} packages.',
                  file=sys.stderr)
            projects = idxpage.projects[:limit]
        list_for_projects(client=client, projects=projects,
                          output_file=output_file)
