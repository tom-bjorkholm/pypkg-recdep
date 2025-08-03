#! /usr/local/bin/python3
"""Print dependency information for a python package in PyPi.org."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

from typing import TextIO, Optional
from os.path import isfile as os_path_isfile
from packaging.requirements import Requirement
from pypkg_recdep.find_pypi_deps import resolve_all_dependencies, \
    find_fulfill_req
from pypkg_recdep.exclude import ExcludeInfo
from pypkg_recdep.pkg_info import Pkgs, PkgKey, PkgInfo


def print_fulfilling_pkg(file: TextIO, req: Requirement,
                         all_deps: Pkgs) -> None:
    """Pint name and version of package fulfilling requirement.

    This is used when a package specifies a requirement that it depends on
    a version greater/smaller than some value. We then wants to print the
    best version fulfilling that requirement, so we search all available
    packages/version for the best match and print that.
    @param file The open file object that we print to.
    @param req A requirement (for a package name and possible version)
    @all_deps A dict of all found dependencies to select a match from.
    """
    key: Optional[PkgKey] = find_fulfill_req(req=req, pkgs=all_deps)
    if key is not None:
        print(f'      - {key.name} version: {str(key.version)}',
              file=file)
    else:
        print('      - (No matching package found!)', file=file)


def print_one_pkg_short(file: TextIO, pkg: PkgKey, data: PkgInfo,
                        all_deps: Pkgs) -> None:
    """Print one package as short list in markdown.

    In this printout only a bullet point list of information for one package
    is printed.
    @param file The open file object that we print to.
    @param pkg The package key (name and version) of the package to print.
    @param data The more complete information on the package.
    @param all_deps A dict of all found dependencies.
    """
    print(f'\n- {pkg.name}', file=file)
    print(f'  - Version: {str(pkg.version)}', file=file)
    print(f'  - Metadata version: {data['metadata_version']}', file=file)
    if len(data['project_urls']) >= 1:
        print('  - project URLs:', file=file)
        for key, val in data['project_urls'].items():
            print(f'    - {key}: {val}', file=file)
    if data['license'] is not None:
        print(f'  - License: {data['license']}', file=file)
    if data['homepage'] is not None:
        print(f'  - Homepage: {data['homepage']}', file=file)
    if data['maintainer'] is not None:
        print(f'  - Maintainer: {data['maintainer']}', file=file)
    print(f'  - Source URL: {data['source_url']}', file=file)
    if data['dependencies']:
        print('  - Dependencies:', file=file)
        for dep in data['dependencies']:
            if dep.specifier is not None:
                print(f'    - {dep.name}  {str(dep.specifier)}',
                      file=file)
            else:
                print(f'    -  {dep.name}', file=file)
            print_fulfilling_pkg(file=file, req=dep, all_deps=all_deps)


def print_one_pkg(file: TextIO,  # pylint: disable=too-many-arguments,too-many-positional-arguments,line-too-long # noqa: E501
                  pkg: PkgKey, data: PkgInfo,
                  mainpkg: bool,
                  all_deps: Pkgs) -> None:
    """Print one package as markdown.

    Print the complete information on a single package as markdown.
    This prints not just a bullet point list but also headings and the
    complete license text.
    @file The open file object that we are printing to.
    @param pkg The package key (name and version) of the package to print.
    @param data The more complete information on the package.
    @param mainpkg Is this the main package that was queried?
    @param all_deps A dict of all found dependencies.
    """
    if mainpkg:
        print(f'\n## Primary package: {pkg.name}', file=file)
    else:
        print(f'### {pkg.name}', file=file)
    print_one_pkg_short(file=file, pkg=pkg, data=data, all_deps=all_deps)
    if data['license_text'] is None:
        return
    if mainpkg:
        print(f'\n### License text ({pkg.name})', file=file)
    else:
        print(f'\n#### License text ({pkg.name})', file=file)
    print(f'\n```` txt\n{data['license_text'].strip()}', file=file)
    print('````\n', file=file)


def print_purl(file: TextIO, pkg: PkgKey) -> None:
    """Write the package url of one package.

    @param file The open file object to print to.
    @param pkg The package (name and version) to print.
    """
    txt = f'pkg:pypi/{pkg.name}'
    if pkg.version:
        txt += f'@{pkg.version}'
    print(txt, file=file)


def print_deps(deps: Pkgs, outfilename: str,
               purls: Optional[str], exclude: ExcludeInfo) -> int:
    """Print app dependencies that have been found.

    Create a markdown file and print to it a description of all the
    dependencies that have been found (recursively) of a package.
    The printout also includes information on the dependency chains,
    license texts etc.
    @param deps The complete information on dependencies to print.
    @param outfilename The name of the output (markdown) file to create.
    @param purls An optional file name of a file to write package urls to.
    @param exclude Information on what packages shall not be fully printed.
    """
    mainpkg, maininfo = list(deps.items())[0]
    kept, excluded = exclude.split_in_keep_and_exclude(pkgs=deps)
    sorted_kept_keys = sorted(list(kept.keys()))
    with open(outfilename, mode='w', encoding='utf8') as file:
        print(f'# Package dependency information for {mainpkg.name}',
              file=file)
        print_one_pkg(file=file, pkg=mainpkg, data=maininfo,
                      mainpkg=True, all_deps=deps)
        print('## Depends (recursively) on packages', file=file)
        if not kept:
            print('\nDepends only on packages that are {exclude.txt}',
                  file=file)
        for pkg in sorted_kept_keys:
            if pkg != mainpkg:
                print_one_pkg_short(file=file, pkg=pkg, data=kept[pkg],
                                    all_deps=deps)
        if excluded:
            print('\n### Also depends on packages ' + exclude.txt, file=file)
            print(f'\nThese dependencies are {exclude.txt}.', file=file)
            print('There will not be any details listed for these.', file=file)
            excluded_keys = sorted(list(excluded.keys()))
            for pkg in excluded_keys:
                print_one_pkg_short(file=file, pkg=pkg, data=excluded[pkg],
                                    all_deps=deps)
        print('\n## Information on dependencies\n', file=file)
        for pkg in sorted_kept_keys:
            if pkg != mainpkg:
                print_one_pkg(file=file, pkg=pkg, data=kept[pkg],
                              mainpkg=False, all_deps=deps)
        print('(End of document.)', file=file)
    if purls:
        if os_path_isfile(purls):
            print(f'File {purls} exists. Appending to it.')
        with open(file=purls, mode='a', encoding='utf8') as file:
            for pkg in sorted_kept_keys:
                print_purl(file=file, pkg=pkg)
    return 0


def print_rec_deps(app_name: str,  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                   metadata_max: str, python_ver: str, outfilename: str,
                   purls: Optional[str], exclude: ExcludeInfo) -> int:
    """Find recursively dependencies and print them.

    Recursively find all dependencies of a package at PyPI.org and print them.
    @param app_name The name of the main package to look for dependencies for.
    @param metadata_max The maximum allowed metadata version for any package.
    @param python_ver The python version that shall be able to run packages.
    @param outfilename The name of the output markdown file to create.
    @param purls Optional name of an output file with package urls.
    @param exclude Information on what packages to exclude full info for.
    """
    deps = resolve_all_dependencies(
        root_package=app_name,
        python_version=python_ver,
        max_metadata_version=metadata_max
    )
    return print_deps(deps=deps, outfilename=outfilename,
                      purls=purls, exclude=exclude)
