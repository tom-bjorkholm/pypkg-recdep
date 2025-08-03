#! /usr/local/bin/python3
"""Get dependencies of a package from PyPI."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

import sys
from tempfile import TemporaryDirectory
import zipfile
import tarfile
from typing import Optional, Final, cast, TypeVar

from requests import HTTPError
from pypi_simple import PyPISimple, DistributionPackage, \
    NoDigestsError, NoMetadataError, DigestMismatchError, NoSuchProjectError
from packaging.markers import default_environment, Environment
from packaging.requirements import Requirement, InvalidRequirement
from packaging.utils import canonicalize_name
from packaging.version import Version
from packaging.metadata import parse_email, RawMetadata
from packaging.licenses import canonicalize_license_expression, \
    InvalidLicenseExpression
from pypkg_recdep.pkg_info import PkgInfo, PkgKey, Pkgs, Requirements, \
    create_pkginfo

T = TypeVar('T', str, tarfile.TarInfo)


def select_given_lic_file(files_in_tar: list[T], meta_lic_files: list[str],
                          pkgid: str, _tinfo: T) -> list[T]:
    """Find specified file names for license text.

    Given the content of a .zip of .tar file and the list of licence file
    names in the metadata file, select the files in the zip/tar to use
    as license files. Print an error message if specified files to not
    exist, but do not abort execution. Return the list of files to use
    as license texts.
    @param files_in_tar  The list of files in tar/zip file.
    @param meta_lic_files The list of license files metioned in metadata.
    @param pkgid  String identifying package (for error message)
    @param _tinfo Actual argument not used, only carries type information.
    """
    ret: list[T] = []
    for i in meta_lic_files:
        if i in files_in_tar:
            ret.append([f for f in files_in_tar if f == i][0])
            continue
        missing = True
        for j in files_in_tar:
            if str(j).endswith('/' + i):
                ret.append(j)
                missing = False
                break
        if missing:
            print(f'Failed to find license text file {i} in package.\n' +
                  f'Package: {pkgid}',
                  file=sys.stderr)
    return ret


def select_default_lic_file(files_in_tar: list[T],
                            pkgid: str, _tinfo: T) -> list[T]:
    """Select best default license file name.

    When metadata does not help us finding files with license text,
    this function looks into list of files in zip/tar file, and
    selects the file we beleave may have license text.
    @param files_in_tar  The list of files in tar/zip file.
    @param pkgid  String identifying package (for error message)
    @param _tinfo Actual argument not used, only carries type information.
    """
    lic_start = ['LICENSE', 'LICENCE', 'COPYING']
    lic_end = ['.txt', '.md', '']
    license_filenames = []
    for start in lic_start:
        for end in lic_end:
            license_filenames.append(start + end)
    for i in license_filenames:
        if i in files_in_tar:
            return [f for f in files_in_tar if f == i]
    for i in license_filenames:
        for j in files_in_tar:
            if str(j).endswith('/' + i):
                return [j]
    print('Failed to find license text in package (no named license file).\n' +
          f'Package: {pkgid}', file=sys.stderr)
    return []


def select_lic_file_names(files_in_tar: list[T],
                          meta_lic_files: Optional[list[str]],
                          pkgid: str, tinfo: T) -> list[T]:
    """Select which file names to use for license text.

    This function handles both the case that we have got licensen file name(s)
    from metadata, and the case with no licence file information from
    metadata. It will return a list of the files to use for license text.
    @meta_lic_files The list of license files metioned in metadata.
    @param pkgid  String identifying package (for error message)
    @param _tinfo Actual argument not used, only carries type information.
    """
    if meta_lic_files is not None:
        assert meta_lic_files is not None
        return select_given_lic_file(files_in_tar=files_in_tar,
                                     meta_lic_files=meta_lic_files,
                                     pkgid=pkgid, _tinfo=tinfo)
    return select_default_lic_file(files_in_tar=files_in_tar, pkgid=pkgid,
                                   _tinfo=tinfo)


def get_lic_text_zip(filename: str, lic_files: Optional[list[str]],
                     pkgid: str) -> str:
    """Get license text from zip file.

    Read license text from downloaded zip file.
    @param filename Name of the downloaded zip file to read from.
    @param lic_files The names of the license files to read as specified
                     in the metadata.
    @param pkgid The name of the package to use in error printouts.
    """
    txt: str = ''
    with zipfile.ZipFile(file=filename, mode='r') as zfile:
        fnames = select_lic_file_names(files_in_tar=zfile.namelist(),
                                       meta_lic_files=lic_files,
                                       pkgid=pkgid, tinfo='a')
        for name in fnames:
            with zfile.open(name=name, mode='r') as licfile:
                txt += licfile.read().decode(encoding='utf-8',
                                             errors='ignore')
    return txt


def get_lic_text_tar(filename: str, lic_files: Optional[list[str]],
                     pkgid: str) -> str:
    """Get license text from .tar.gz file.

    Read license text from downloaded .tar.gz file.
    @param filename Name of the downloaded tar file to read from.
    @param lic_files The names of the license files to read as specified
                     in the metadata.
    @param pkgid The name of the package to use in error printouts.
    """
    txt: str = ''
    with tarfile.open(name=filename, mode='r:gz') as tfile:
        fnames = select_lic_file_names(files_in_tar=tfile.getmembers(),
                                       meta_lic_files=lic_files,
                                       pkgid=pkgid, tinfo=tarfile.TarInfo())
        for name in fnames:
            iob = tfile.extractfile(member=name)
            if iob:
                assert iob is not None
                txt += iob.read().decode(encoding='utf-8', errors='ignore')
    return txt


def get_license_text(client: PyPISimple, pkg: DistributionPackage,
                     lic_files: Optional[list[str]]) -> str:
    """Get license text.

    Get license text by downloading the package file and then extracting the
    text in the license files in the package.
    @param client The PyPISImple client to use for server connection.
    @param pkg The distribution package information as retrieced from PyPI.
    @param lic_files The list of license files retrieved from package
                     metadata.
    """
    with TemporaryDirectory() as dirname:
        fname = dirname + '/' + pkg.filename
        try:
            client.download_package(pkg=pkg, path=fname, timeout=120.0)
            if fname.endswith(('.whl', '.zip')):
                return get_lic_text_zip(filename=fname, lic_files=lic_files,
                                        pkgid=pkg.filename)
            if fname.endswith(('.tar.gz', '.tgz')):
                return get_lic_text_tar(filename=fname, lic_files=lic_files,
                                        pkgid=pkg.filename)
            print(f'Do not know how to unpack {pkg.filename}',
                  file=sys.stderr)
        except (HTTPError, NoDigestsError, DigestMismatchError) as exc:
            print(f'Failed to download package {pkg.project} {pkg.version}\n',
                  f'    {str(exc)}', file=sys.stderr)
    return ''


def get_requirements(raw: RawMetadata, pyenv: Environment) -> Requirements:
    """Get requirements from metadata filtered through environment.

    Look at the raw metadata for a package and determine which requirements
    are relevant for running this package in specified environment.
    (Environment does for instance have information about target python
    version.) Returns the relevant requirements.
    @param raw The raw metadata to extract requirements from.
    @param pyenv A specification of the target python environment to use
                 for filtering out which requirements are relevant.
    """
    if 'requires_dist' not in raw:
        return []
    reqs: Optional[list[str]] = raw['requires_dist']
    if not reqs:
        return []
    ret: Requirements = []
    for req in reqs:
        try:
            requirement = Requirement(req)
            if not requirement.marker:
                ret.append(requirement)
                continue
            assert requirement.marker is not None
            assert pyenv is not None
            if requirement.marker.evaluate(cast(dict[str, str], pyenv)):
                ret.append(requirement)
        except InvalidRequirement as exc:
            print(f'Ignoring invalid requirement: {req}\n' +
                  f'    {str(exc)}', file=sys.stderr)
    return ret


def find_fulfill_req(req: Requirement, pkgs: Pkgs) -> Optional[PkgKey]:
    """Check if any of the packages fullfills the requirement.

    Check a requirement to see if any of the collected packages already
    fulfills the requirement. Returns the package key to the first found
    package that fulfills the requirement, or None if no package fulfills
    the requirement.
    @param req The requirement to try to fulfill.
    @param pkgs The collected package information to search through.
    """
    for pkg_key in pkgs.keys():
        if pkg_key.name == req.name:
            if req.specifier.contains(pkg_key.version):
                return pkg_key
    return None


class NoMatchingPackage(KeyError):
    """No package matches requirement."""


def py_oks(pkgs: list[DistributionPackage],
           pyversion: Version) -> list[DistributionPackage]:
    """Filter out the packages that are OK for python version.

    Take a list of packages and filter out only the subset that can be run
    on the specified python version. Returns a list of packages that can
    be run on the specified python version.
    @param pkgs A list of packages to check.
    @param pyversion The python version to check if packages can run on.
    """
    ret: list[DistributionPackage] = []
    for pkg in pkgs:
        if pkg.requires_python is None:
            ret.append(pkg)
            continue
        req = Requirement('python ' + pkg.requires_python)
        if req.specifier.contains(pyversion):
            ret.append(pkg)
    if not ret:
        raise NoMatchingPackage('No package that can run python version.')
    return ret


def meta_ok(client: PyPISimple, pkgs: list[DistributionPackage],
            metaversion: Optional[Version]) \
                 -> tuple[DistributionPackage, str]:
    """Get first package with OK metadata and its metadata.

    Go through list of packages in order and try to get metadata for
    each package in turn. When finding the first package with OK
    metadata the search stops and the package and its metadata is returned.
    @param client The client connected to the PyPI server.
    @param pkgs The list of packages to try to find one with OK metadata in.
    @param metaversion The maximum allowed metadata version.
    """
    no_meta: list[DistributionPackage] = []
    for pkg in pkgs:
        if not pkg.has_metadata:
            no_meta.append(pkg)
        else:
            try:
                meta = client.get_package_metadata(pkg, timeout=30.0)
                if not metaversion:
                    return (pkg, meta)
                raw, _ = parse_email(meta)
                ver = raw['metadata_version']
                if not ver:
                    no_meta.append(pkg)
                else:
                    if Version(ver) <= metaversion:
                        return (pkg, meta)
            except (NoMetadataError, HTTPError, NoDigestsError,
                    DigestMismatchError) as exc:
                print('Failed to get metadata for ' +
                      f'{pkg.project} {pkg.version}\n' +
                      f'    {str(exc)}', file=sys.stderr)
                no_meta.append(pkg)
    if no_meta:
        return (no_meta[0], '')
    raise NoMatchingPackage('All packages have not OK metadata version.')


def set_pkginfo_from_raw(info: PkgInfo, raw: RawMetadata,
                         pyenv: Environment) -> None:
    """Set PkgInfo data from raw from metadata.

    Look for information in raw metadata and store relevant information
    in the info parameter pf PkgInfo type. Things like requirements, URLs,
    license etc is read from metadata and stored.
    @param info Output parameter. The information about the package.
    @param raw The raw metadata to extract information from.
    @param pyenv Information about target environment used to determine which
                 requirements are relevant.
    """
    if 'metadata_version' in raw:
        info['metadata_version'] = Version(raw['metadata_version'])
    if 'license' in raw and raw['license']:
        try:
            info['license'] = \
                str(canonicalize_license_expression(raw['license']))
        except InvalidLicenseExpression:
            info['license'] = raw['license']
    if 'project_urls' in raw:
        info['project_urls'] = raw['project_urls']
        for key in ['Source', 'source', 'GitHub', 'github', 'Repository',
                    'repository', 'Code', 'code', 'Homepage', 'homepage']:
            if key in raw['project_urls']:
                info['source_url'] = raw['project_urls'][key]
                break
    if 'home_page' in raw:
        info['homepage'] = raw['home_page']
    if 'maintainer' in raw:
        info['maintainer'] = raw['maintainer']
    info['dependencies'] = get_requirements(raw=raw, pyenv=pyenv)


def get_best_pkg(client: PyPISimple, req: Requirement, pyversion: Version,
                 metaversion: Optional[Version],
                 pyenv: Environment) -> PkgInfo:
    """Get the best package from PyPI that fulfill requirements.

    Get PkgInfo on the best (newest) package in PyPI server that fulfill the
    requirement (pkg name and version), and also runs on the specified python
    version and that has a metadata version that is allowed. A package with
    higher version number is considered better.
    Returns information (PkgInfo) on the best found package.
    @param client The client connnected to the PyPI server to query.
    @param req The requirement on the package (package name and version).
    @param pyversion The python version number on the target to run package.
    @param metaversion Optionally the highest allowed metadata version.
    @param pyenv The python environment specifiying the target.
    """
    page = client.get_project_page(req.name, timeout=30.0)
    pkgs = sorted(page.packages,
                  key=lambda x: Version(x.version)
                  if x.version else Version('0'),
                  reverse=True)
    if not pkgs:
        raise NoMatchingPackage(f'No match for {str(req.name)}')
    pkgs_reqok = [p for p in pkgs if p.version and
                  req.specifier.contains(p.version)]
    if not pkgs_reqok:
        raise NoMatchingPackage(f'No match for {str(req)}')
    pkgs_pyok = py_oks(pkgs=pkgs_reqok, pyversion=pyversion)
    pkg, meta = meta_ok(client=client, pkgs=pkgs_pyok,
                        metaversion=metaversion)
    assert pkg.version is not None
    assert pkg.project is not None
    ret: PkgInfo = create_pkginfo(key=PkgKey(pkg.project, pkg.version))
    if not meta:
        return ret
    raw, _ = parse_email(meta)
    set_pkginfo_from_raw(info=ret, raw=raw, pyenv=pyenv)
    lic_files: Optional[list[str]] = raw.get('license_files', None)
    ret['license_text'] = get_license_text(client=client,
                                           pkg=pkg, lic_files=lic_files)
    return ret


def get_environment(pyversion: Version) -> Environment:
    """Get environemnt with specified python version.

    Get the python environment specification that is running the code.
    Replace the python version information in environment with the supplied
    python version, and return that environmnet specification.
    @param pyversion The python version to use (instead of running python).
    """
    env: Environment = default_environment()
    env['python_full_version'] = str(pyversion) + '.0'
    env['python_version'] = str(pyversion)
    return env


def resolve_all_dependencies(root_package: str,  # pylint: disable=too-many-locals # noqa: E501
                             python_version: str,
                             max_metadata_version: Optional[str] = None
                             ) -> Pkgs:
    """Resolve all dependencies of a package in PyPI.

    Connect to PyPI.org and get information about specified package.
    Get the best (highest version number) that fulfill requirement on python
    version and metadata version. Then look at all the packages required
    by this package and do the same for those packages, and build a list
    of package information for packages needed to run the specified package.
    Then continue to find information on all packages required by some package
    and add that information to the list, until all packages in the list only
    depend on packages in the list. Then return the list with package
    information.
    @param root_package The name of package to resolve all dependencies for.
    @param python_version Use only packages that can run on this
                          python version.
    @param max_metadata_version Use only packages that has this or
                                lower metadata version.
    """
    ret: Pkgs = {}
    visited: Requirements = []
    queue: Requirements = [Requirement(canonicalize_name(root_package))]
    pyversion: Final[Version] = Version(python_version)
    metaversion: Final[Optional[Version]] = \
        Version(max_metadata_version) if max_metadata_version else None
    pyenv: Final[Environment] = get_environment(pyversion)
    with PyPISimple() as client:
        while queue:
            req = queue.pop()
            if req in visited or find_fulfill_req(req, ret) is not None:
                continue
            try:
                pkginfo: PkgInfo = \
                    get_best_pkg(client=client, req=req,
                                 pyversion=pyversion,
                                 metaversion=metaversion, pyenv=pyenv)
                for subreq in pkginfo['dependencies']:
                    if subreq not in visited and subreq not in queue:
                        queue.insert(0, subreq)
                ret[pkginfo['key']] = pkginfo
            except (NoMatchingPackage, NoSuchProjectError) as exc:
                print(f'No matching package found for {str(req)}\n' +
                      f'    {str(exc)}', file=sys.stderr)
    return ret
