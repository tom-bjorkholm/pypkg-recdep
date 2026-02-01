#! /usr/local/bin/python3
"""Print dependency information for a python package in PyPi.org."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

from typing import TextIO, Optional, NamedTuple
from os.path import isfile as os_path_isfile
from packaging.requirements import Requirement
from mformat.factory import create_mf, OptArgs
from mformat.mformat import MultiFormat
from pypkg_recdep.find_pypi_deps import resolve_all_dependencies, \
    find_fulfill_req
from pypkg_recdep.exclude import ExcludeInfo
from pypkg_recdep.pkg_info import Pkgs, PkgKey, PkgInfo


def print_fulfilling_pkg(mformat: MultiFormat, req: Requirement,
                         all_deps: Pkgs) -> None:
    """Pint name and version of package fulfilling requirement.

    This is used when a package specifies a requirement that it depends on
    a version greater/smaller than some value. We then wants to print the
    best version fulfilling that requirement, so we search all available
    packages/version for the best match and print that.
    @param mformat The MultiFormat object that we print to.
    @param req A requirement (for a package name and possible version)
    @all_deps A dict of all found dependencies to select a match from.
    """
    key: Optional[PkgKey] = find_fulfill_req(req=req, pkgs=all_deps)
    if key is not None:
        mformat.start_bullet_item(f'{key.name} version: {str(key.version)}',
                                  level=4)
    else:
        mformat.start_bullet_item('(No matching package found!)', level=4)


def print_one_pkg_short(mformat: MultiFormat, pkg: PkgKey, data: PkgInfo,
                        all_deps: Pkgs) -> None:
    """Print one package as short list in markdown.

    In this printout only a bullet point list of information for one package
    is printed.
    @param mformat The MultiFormat object that we print to.
    @param pkg The package key (name and version) of the package to print.
    @param data The more complete information on the package.
    @param all_deps A dict of all found dependencies.
    """
    mformat.start_bullet_item(f'{pkg.name}', level=1)
    mformat.start_bullet_item(f'Version: {str(pkg.version)}', level=2)
    mformat.start_bullet_item(f'Metadata version: {data['metadata_version']}',
                              level=2)
    if len(data['project_urls']) >= 1:
        mformat.start_bullet_item('project URLs:')
        for key, val in data['project_urls'].items():
            mformat.start_bullet_item(f'{key}: ', level=3)
            mformat.add_url(url=val)
    if data['license'] is not None:
        mformat.start_bullet_item(f'License: {data['license']}', level=2)
    if data['homepage'] is not None:
        mformat.start_bullet_item('Homepage: ', level=2)
        mformat.add_url(url=data['homepage'])
    if data['maintainer'] is not None:
        mformat.start_bullet_item(f'Maintainer: {data['maintainer']}', level=2)
    mformat.start_bullet_item('Source URL: ', level=2)
    if data['source_url'] is not None:
        mformat.add_url(url=data['source_url'])
    else:
        mformat.add_text('None')
    if data['dependencies']:
        mformat.start_bullet_item('Dependencies:', level=2)
        for dep in data['dependencies']:
            if dep.specifier:
                mformat.start_bullet_item(f'{dep.name}  {str(dep.specifier)}',
                                          level=3)
            else:
                mformat.start_bullet_item(f'{dep.name}', level=3)
            print_fulfilling_pkg(mformat=mformat, req=dep, all_deps=all_deps)


def print_one_pkg(mformat: MultiFormat,  # pylint: disable=too-many-arguments,too-many-positional-arguments,line-too-long # noqa: E501
                  pkg: PkgKey, data: PkgInfo,
                  mainpkg: bool,
                  all_deps: Pkgs) -> None:
    """Print one package as markdown.

    Print the complete information on a single package as markdown.
    This prints not just a bullet point list but also headings and the
    complete license text.
    @mformat The MultiFormat object that we are printing to.
    @param pkg The package key (name and version) of the package to print.
    @param data The more complete information on the package.
    @param mainpkg Is this the main package that was queried?
    @param all_deps A dict of all found dependencies.
    """
    if mainpkg:
        mformat.start_heading(text=f'Primary package: {pkg.name}', level=2)
    else:
        mformat.start_heading(text=f'{pkg.name}', level=3)
    print_one_pkg_short(mformat=mformat, pkg=pkg, data=data,
                        all_deps=all_deps)
    if data['license_text'] is None:
        return
    mformat.start_heading(text=f'License text ({pkg.name})',
                          level=3 if mainpkg else 4)
    mformat.write_code_block(text=data['license_text'].strip(),
                             programming_language='txt')


def print_purl(file: TextIO, pkg: PkgKey) -> None:
    """Write the package url of one package.

    @param file The open file object to print to.
    @param pkg The package (name and version) to print.
    """
    txt = f'pkg:pypi/{pkg.name}'
    if pkg.version:
        txt += f'@{pkg.version}'
    print(txt, file=file)


class OutputSpec(NamedTuple):
    """Specification for output."""

    outfileformat: str
    outfilename: str
    url_as_text: bool
    purlfilename: Optional[str]


def file_exists_cb(filename: str) -> None:
    """Handle case when output file exists.

    Returning allows overwriting the file.
    Raises FileExistsError if overwrite is not allowed.
    @param filename The name of the file that exists.
    """
    answer = input(f'File {filename} exists. Overwrite? (y/n): ')
    if answer.lower() in ['y', 'ye', 'yes', 'yes!']:
        return
    raise FileExistsError(f'File {filename} exists.')


def print_deps(deps: Pkgs, outputspec: OutputSpec,
               exclude: ExcludeInfo) -> int:
    """Print app dependencies that have been found.

    Create a markdown file and print to it a description of all the
    dependencies that have been found (recursively) of a package.
    The printout also includes information on the dependency chains,
    license texts etc.
    @param deps The complete information on dependencies to print.
    @param outputspec The specification for outputing the results.
    @param exclude Information on what packages shall not be fully printed.
    """
    if not deps:
        return 0
    mainpkg, maininfo = list(deps.items())[0]
    kept, excluded = exclude.split_in_keep_and_exclude(pkgs=deps)
    sorted_kept_keys = sorted(list(kept.keys()))
    optargs: OptArgs = {'file_exists_callback': file_exists_cb}
    with create_mf(format_name=outputspec.outfileformat,
                   file_name=outputspec.outfilename,
                   url_as_text=outputspec.url_as_text,
                   args=optargs) as mf:
        mf.start_heading(text='Package dependency information for',
                         level=1)
        mf.add_text(mainpkg.name)
        print_one_pkg(mformat=mf, pkg=mainpkg, data=maininfo,
                      mainpkg=True, all_deps=deps)
        mf.start_heading(text='Depends (recursively) on packages', level=2)
        if not kept:
            mf.start_paragraph(text='Depends only on packages that '
                               f'are {exclude.txt}')
        for pkg in sorted_kept_keys:
            if pkg != mainpkg:
                print_one_pkg_short(mformat=mf, pkg=pkg, data=kept[pkg],
                                    all_deps=deps)
        if excluded:
            mf.start_heading(text=f'Also depends on packages {exclude.txt}',
                             level=3)
            mf.start_paragraph(text=f'These dependencies are {exclude.txt}.')
            mf.add_text('There will not be any details listed for these.')
            excluded_keys = sorted(list(excluded.keys()))
            for pkg in excluded_keys:
                print_one_pkg_short(mformat=mf, pkg=pkg, data=excluded[pkg],
                                    all_deps=deps)
        mf.start_heading(text='Information on dependencies', level=2)
        for pkg in sorted_kept_keys:
            if pkg != mainpkg:
                print_one_pkg(mformat=mf, pkg=pkg, data=kept[pkg],
                              mainpkg=False, all_deps=deps)
        mf.start_paragraph('(End of document.)')
    if outputspec.purlfilename:
        if os_path_isfile(outputspec.purlfilename):
            print(f'File {outputspec.purlfilename} exists. Appending to it.')
        with open(file=outputspec.purlfilename, mode='a',
                  encoding='utf8') as file:
            for pkg in sorted_kept_keys:
                print_purl(file=file, pkg=pkg)
    return 0


def print_rec_deps(app_name: str, metadata_max: str, python_ver: str,
                   outputspec: OutputSpec, exclude: ExcludeInfo) -> int:
    """Find recursively dependencies and print them.

    Recursively find all dependencies of a package at PyPI.org and print them.
    @param app_name The name of the main package to look for dependencies for.
    @param metadata_max The maximum allowed metadata version for any package.
    @param python_ver The python version that shall be able to run packages.
    @param outputspec The specification for outputing the results.
    @param exclude Information on what packages to exclude full info for.
    """
    deps = resolve_all_dependencies(
        root_package=app_name,
        python_version=python_ver,
        max_metadata_version=metadata_max
    )
    return print_deps(deps=deps, outputspec=outputspec, exclude=exclude)
