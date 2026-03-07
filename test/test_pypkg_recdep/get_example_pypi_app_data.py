"""Get test data from pypi on package and store to files."""

import sys
import pickle
from pypi_simple import PyPISimple
from packaging.version import Version
from packaging.metadata import parse_email


def pickle_to_file(dirname: str, fname_base: str, obj_name: str,
                   obj: object) -> None:
    """Pickle the object to file with constructed name."""
    fname = dirname + '/' + fname_base + '_' + obj_name + '.pkl'
    with open(file=fname, mode='wb') as file:
        pickle.dump(obj, file=file, protocol=pickle.HIGHEST_PROTOCOL)


def get_example_pypi_app_data(pkgname: str, version: Version,
                              fname_base: str, dirname: str) -> None:
    """Get test data from pypi on package and store to files."""
    with PyPISimple() as client:
        page = client.get_project_page(pkgname, timeout=120.0)
        pkgs = sorted(page.packages,
                      key=lambda x: Version(x.version)
                      if x.version else Version('0'),
                      reverse=True)
        if not pkgs or len(pkgs) < 1:
            print('No packages found for:', pkgname, file=sys.stderr)
            sys.exit(1)
        pkg = None
        for pkg_iter in pkgs:
            if pkg_iter.version and Version(pkg_iter.version) == version:
                pkg = pkg_iter
                break
        if pkg is None:
            print(f'No version {version} for package: {pkgname}',
                  file=sys.stderr)
            sys.exit(1)
        if not pkg.has_metadata:
            print('No metadata for package:', pkgname, file=sys.stderr)
            sys.exit(1)
        meta = client.get_package_metadata(pkg, timeout=120.0)
        raw, _ = parse_email(meta)
        pickle_to_file(dirname=dirname, fname_base=fname_base,
                       obj_name='page', obj=page)
        pickle_to_file(dirname=dirname, fname_base=fname_base,
                       obj_name='pkg', obj=pkg)
        pickle_to_file(dirname=dirname, fname_base=fname_base,
                       obj_name='meta', obj=meta)
        pickle_to_file(dirname=dirname, fname_base=fname_base,
                       obj_name='raw', obj=raw)


def example_data_from_pypi() -> None:
    """Get test data from pypi on sevaral packages and store to files."""
    dir_name = 'test/test_pypkg_recdep'
    to_get = [('excel-list-transform', '0.8.3', 'elt'),
              ('jaraco.itertools', '6.4.3', 'jai'),
              ('pytest', '9.0.0', 'pyt')]
    for (pkg_name, ver, fbase) in to_get:
        get_example_pypi_app_data(pkgname=pkg_name, version=Version(ver),
                                  fname_base=fbase, dirname=dir_name)


if __name__ == '__main__':
    example_data_from_pypi()
