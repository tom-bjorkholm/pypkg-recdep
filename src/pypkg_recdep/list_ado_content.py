#! /usr/local/bin/python3
"""Get and list python package content of ADO server."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

from csv import writer
from typing import Optional, TypeAlias, NamedTuple
from typing import Union, List, Dict, cast  # pylint: disable=unused-import
from copy import deepcopy
import sys
import base64
import requests
import urllib3

urllib3.disable_warnings()

#
# Some documentation hints this is based on:
#
# Look for feeds:
# https://learn.microsoft.com/en-us/rest/api/azure/devops/artifacts/\
# feed-management/get-feeds?view=azure-devops-server-rest-7.1
#
# https://learn.microsoft.com/en-us/rest/api/azure/devops/artifacts/\
# artifact-details/get-packages?view=azure-devops-server-rest-7.1
#
# PAT:
# https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/\
# use-personal-access-tokens-to-authenticate?\
# view=azure-devops-2022&tabs=Windows
#

JsonType: TypeAlias = \
    'Union[None, int, str, bool, List[JsonType], Dict[str, JsonType]]'


class SinglePkgInfo(NamedTuple):
    """Information about a single package in single version."""

    name: str
    version: str
    metadata_version: str
    package_type: str
    file_name: str


PkgVersions: TypeAlias = list[SinglePkgInfo]


class PkgInfo(NamedTuple):
    """Information about all versions of a package."""

    name: str
    versions: PkgVersions


Pkgs: TypeAlias = list[PkgInfo]


class UrlInfo(NamedTuple):
    """Information about ADO package repo."""

    instance: str
    collection: str
    pat_file: str


def print_pkgs(pkgs: Pkgs, file_name: str) -> None:
    """Print packages into CSV file.

    @param pkgs Information on packages to print.
    @param file_name Name (path) of file to write CSV data to.
    """
    with open(file=file_name, mode='w', encoding='utf-8') as file:
        writerobj = writer(file, dialect='unix')
        writerobj.writerow(['Name', 'Name of version', 'Version',
                            'Metadata version', 'package type', 'file name'])
        for pkg in pkgs:
            for ver in pkg.versions:
                writerobj.writerow([pkg.name, ver.name, ver.version,
                                    ver.metadata_version, ver.package_type,
                                    ver.file_name])
    print(f'\nWrote results to {file_name}', file=sys.stderr)


get_headers_per_file: dict[str, dict[str, str]] = {}


def get_headers(pat_file: str) -> dict[str, str]:
    """Get headers to use for REST request based on PAT in file.

    The personal access token(s) (PAT) is in file(s). Get the HTTPS headers
    to use based on the PAT file name. A cache is used to read each PAT
    file only once.
    @param pat_file File name of file with PAT to use.
    """
    if pat_file is None:
        return {}
    if pat_file in get_headers_per_file:
        return get_headers_per_file[pat_file]
    pat: Optional[str] = None
    try:
        with open(file=pat_file, mode='r', encoding='utf-8') as file:
            pat = file.read()
    except FileNotFoundError:
        print(f'PAT file "{pat_file}" not found.',
              file=sys.stderr)
        sys.exit(1)
    encoded_pat = base64.b64encode((':' + pat).encode()).decode()
    get_headers_per_file[pat_file] = {'Authorization': 'Basic ' + encoded_pat}
    return get_headers_per_file[pat_file]


class RestException(RuntimeError):
    """Exception querying REST API."""


def get_from_rest(url: str, pat_file: str) -> JsonType:
    """Do a REST request and return result value.

    Also check that response to REST query is OK.
    @param url The composed URL of the query.
    @param pat_file The file with the personal acccess token to use.
    """
    response = requests.get(url=url, headers=get_headers(pat_file),
                            timeout=60, verify=False)
    if not response.ok:
        print(f'Failed REST request: {url}', file=sys.stderr)
        print(f'Reply: {response}', file=sys.stderr)
        raise RestException(f'Failed REST request: {response}')
    return cast(JsonType, response.json())


def get_value_from_rest(url: str, pat_file: str) -> list[JsonType]:
    """Get value element from REST response to URL get.

    Send REST query. Check that result is OK and extract value from answer.
    @param url The composed URL of the REST query.
    @param pat_file The file with the personal acccess token to use.
    """
    resp = get_from_rest(url=url, pat_file=pat_file)
    assert isinstance(resp, dict)
    val = resp['value']
    assert isinstance(val, list)
    return val


def get_feed_id(url_info: UrlInfo,
                lookup_name: str = 'packages') -> str:
    """Get the feed ID to query for packages.

    We have to send an initial query to the Azure Dev Ops server to get
    the feed ID to use in queries for packages. This function does that
    query.
    @paralm url_info Infromation about server to build URL from.
    @param lookup_name The name of the feed we want ID for.
    """
    url = f'https://{url_info.instance}/{url_info.collection}/_apis/packaging'
    url += '/feeds?api-version=7.1'
    value = get_value_from_rest(url=url, pat_file=url_info.pat_file)
    assert isinstance(value, list)
    for feed in value:
        assert isinstance(feed, dict)
        if feed['fullyQualifiedName'] == lookup_name:
            feed_id = feed['id']
            assert isinstance(feed_id, str)
            print(f'Found feed ID "{feed_id}"', file=sys.stderr)
            return feed_id
    print('Feed ID not found', file=sys.stderr)
    raise RestException('Feed ID not found')


def get_from_meta(meta: dict[str, JsonType], key: str) -> str:
    """Get value for key from meta-data.

    Look up a value in metadata dictionary and assure that it is a string.
    Print and error message if the key does not exist in metadata.
    @param meta The metadata dictionary to look up in.
    @param key The key to get the value for.
    """
    if key in meta:
        val = meta[key]
        assert isinstance(val, str)
        return val
    print(f'no "{key}" in: {meta}\n\n\n', file=sys.stderr)
    return ''


def parse_meta(ver: dict[str, JsonType]) -> tuple[str, str, str]:
    """Get name, version and metadata version from version JSON part.

    Parse the metadata dictionary and find values for name, version, and
    metadata version. Return a tuple with name, version and metadata version.
    @param ver The metadata dictionary for a version of a package.
    """
    if 'protocolMetadata' not in ver:
        return ('', '', '')
    meta = ver['protocolMetadata']
    assert isinstance(meta, dict)
    if 'data' not in meta:
        print('No data in meta', file=sys.stderr)
        return ('', '', '')
    data = meta['data']
    assert isinstance(data, dict)
    name = get_from_meta(meta=data, key='Name')
    version = get_from_meta(meta=data, key='Version')
    metadata_version = get_from_meta(meta=data,
                                     key='MetadataVersion')
    return (name, version, metadata_version)


def parse_fileinfo(pfile: dict[str, JsonType], name: str, version: str,
                   metaversion: str,
                   include_types: list[str]) -> Optional[SinglePkgInfo]:
    """Parse from file info in JSON into SinglePkgInfo if OK.

    Take the JSON part that that describes a file and parse it into
    SinglePkgInfo. Returns SinglePkgInfo only if correct file type found.
    @param pfile JSON part that is an element of files.
    @param name The name of the package
    @param version The version of this package.
    @param metaversion The metadata version.
    @param include_type A list of file types to include in listing.
    """
    fname = get_from_meta(meta=pfile, key='name')
    assert isinstance(fname, str)
    if 'protocolMetadata' not in pfile:
        print(f'No protocolMetadata in pfile name={name}',
              file=sys.stderr)
        return None
    pmeta = pfile['protocolMetadata']
    assert isinstance(pmeta, dict)
    if 'data' not in pmeta:
        print(f'No data in protocolMetadata name={name}',
              file=sys.stderr)
        return None
    pmdata = pmeta['data']
    assert isinstance(pmdata, dict)
    file_type = get_from_meta(meta=pmdata, key='FileType')
    assert isinstance(file_type, str)
    if file_type == '':
        print(f'No file type in protocolMetadata name={name}',
              file=sys.stderr)
        return None
    ok_file_type: bool = True
    if include_types:
        ok_file_type = False
        for i in include_types:
            if i.lower() in file_type.lower():
                ok_file_type = True
                sys.stderr.write(':')
    if ok_file_type:
        return SinglePkgInfo(name=name, version=version,
                             metadata_version=metaversion,
                             package_type=file_type,
                             file_name=fname)
    return None


def get_pkg_versions(url: str, include_types: list[str],
                     pat_file: str) -> PkgVersions:
    """Get informations on all versions of a specific package.

    Returns a list of information on versions of a package.
    @param url The URL to the package to get versions for.
    @param include_types A list of file types to include in listing.
    @param pat_file The file name (path) with the personal access token.
    """
    verurl = deepcopy(url) + '/Versions'
    value = get_value_from_rest(url=verurl, pat_file=pat_file)
    ret: PkgVersions = []
    for ver in value:
        assert isinstance(ver, dict)
        (name, version, metadata_version) = parse_meta(ver)
        if name == '' and version == '':
            continue
        if 'files' not in ver:
            print(ver, file=sys.stderr)
            print(f'No files in ver name={name}',
                  file=sys.stderr)
            continue
        pfiles = ver['files']
        assert isinstance(pfiles, list)
        for pfile in pfiles:
            assert isinstance(pfile, dict)
            single_pkg = parse_fileinfo(pfile=pfile, name=name,
                                        version=version,
                                        metaversion=metadata_version,
                                        include_types=include_types)
            if single_pkg is not None:
                ret.append(single_pkg)
    return ret


def get_pkgs(url_info: UrlInfo, project: Optional[str],
             include_types: list[str]) -> Pkgs:
    """Get information on all packages of correct types.

    Returns a list of all packages on server/URL matching the file types
    specified in include_types.
    @param url_info The information needed to build and use URL to server.
    @param project An optional project to use in URL.
    @param include_types A list of the file types to include in answer.
    """
    url = f'https://{url_info.instance}/{url_info.collection}/'
    if project is not None:
        url += f'{project}/'
    feed_id = get_feed_id(url_info=url_info)
    url += f'_apis/packaging/Feeds/{feed_id}/packages?api-version=7.1'
    value = get_value_from_rest(url=url, pat_file=url_info.pat_file)
    ret: Pkgs = []
    for package in value:
        assert isinstance(package, dict)
        ver_url = package['url']
        assert isinstance(ver_url, str)
        name = package['normalizedName']
        assert isinstance(name, str)
        vers: PkgVersions = get_pkg_versions(url=ver_url,
                                             include_types=include_types,
                                             pat_file=url_info.pat_file)
        ret.append(PkgInfo(name=name, versions=vers))
        sys.stderr.write('.')
        sys.stderr.flush()
    return ret


def list_ado_content(file_name: str, url_info: UrlInfo,
                     project: Optional[str],
                     include_types: list[str]) -> int:
    """Create CSV file with python packages in ADO.

    Get information on python packages available in Azure Dev Ops server.
    Only packages with the requested file type(s) will be included.
    Print the information into a comma separated values (CSV) file.
    The file created can be used as exclude-file ExcludeInfo on exclude.py.
    @param file_name The name (path) of the CSV file to create.
    @param url_info The information needed to create/use URL to ADO server.
    @param project An optional project to add to URL.
    @param include_types A list of file types (wheel etc.) to include.
    """
    print(f'Output file name: {file_name}', file=sys.stderr)
    print(f'instance: {url_info.instance}', file=sys.stderr)
    print(f'collection: {url_info.collection}', file=sys.stderr)
    print(f'project: {project}', file=sys.stderr)
    print(f'include_types: {include_types}', file=sys.stderr)
    print(f'pat_file: {url_info.pat_file}', file=sys.stderr)
    pkgs = get_pkgs(url_info=url_info,
                    project=project, include_types=include_types)
    print_pkgs(pkgs=pkgs, file_name=file_name)
    return 0
