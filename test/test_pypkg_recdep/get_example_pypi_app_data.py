"""Get test data from pypi on package and store to files."""

import sys
import pickle
from pypi_simple import PyPISimple
from packaging.version import Version
from packaging.metadata import parse_email


def get_example_pypi_app_data(pkgname: str, version: Version,
                              page_fname: str, pkg_fname: str,
                              raw_fname: str):
    """Get test data from pypi on package and store to files."""
    with PyPISimple() as client:
        page = client.get_project_page(pkgname, timeout=30)
        pkgs = sorted(page.packages,
                      key=lambda x: Version(x.version)
                      if x.version else Version('0'),
                      reverse=True)
        if not pkgs or len(pkgs) < 1:
            print('No packages found for:', pkgname, file=sys.stderr)
            sys.exit(1)
        pkg = None
        for pkg_iter in pkgs:
            if Version(pkg_iter.version) == version:
                pkg = pkg_iter
                break
        if pkg is None:
            print(f'No version {version} for package: {pkgname}',
                  file=sys.stderr)
        if not pkg.has_metadata:
            print('No metadata for package:', pkgname, file=sys.stderr)
            sys.exit(1)
        meta = client.get_package_metadata(pkg, timeout=30.0)
        raw, _ = parse_email(meta)
        with open(file=page_fname, mode='wb') as file:
            pickle.dump(page, file=file, protocol=pickle.HIGHEST_PROTOCOL)
        with open(file=pkg_fname, mode='wb') as file:
            pickle.dump(pkg, file=file, protocol=pickle.HIGHEST_PROTOCOL)
        with open(file=raw_fname, mode='wb') as file:
            pickle.dump(raw, file=file, protocol=pickle.HIGHEST_PROTOCOL)


if __name__ == '__main__':
    DIR_NAME = 'test/test_pypkg_recdep/'
    get_example_pypi_app_data(pkgname='excel-list-transform',
                              version=Version('0.8.3'),
                              page_fname=DIR_NAME + 'elt_page.pkl',
                              pkg_fname=DIR_NAME + 'elt_pkg.pkl',
                              raw_fname=DIR_NAME + 'elt_raw.pkl')
    get_example_pypi_app_data(pkgname='jaraco.itertools',
                              version=Version('6.4.3'),
                              page_fname=DIR_NAME + 'jai_page.pkl',
                              pkg_fname=DIR_NAME + 'jai_pkg.pkl',
                              raw_fname=DIR_NAME + 'jai_raw.pkl')
    get_example_pypi_app_data(pkgname='pytest',
                              version=Version('9.0.0'),
                              page_fname=DIR_NAME + 'pyt_page.pkl',
                              pkg_fname=DIR_NAME + 'pyt_pkg.pkl',
                              raw_fname=DIR_NAME + 'pyt_raw.pkl')
