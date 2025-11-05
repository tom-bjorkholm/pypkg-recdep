"""Get test data from pypi on package and store to files."""

import sys
import pickle
from pypi_simple import PyPISimple
from packaging.version import Version
from packaging.metadata import parse_email


def get_example_pypi_app_data(pkgname: str, page_fname: str, raw_fname):
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
        if not pkgs[0].has_metadata:
            print('No metadata for package:', pkgname, file=sys.stderr)
            sys.exit(1)
        meta = client.get_package_metadata(pkgs[0], timeout=30.0)
        raw, _ = parse_email(meta)
        with open(file=page_fname, mode='wb') as file:
            pickle.dump(page, file=file, protocol=pickle.HIGHEST_PROTOCOL)
        with open(file=raw_fname, mode='wb') as file:
            pickle.dump(raw, file=file, protocol=pickle.HIGHEST_PROTOCOL)


if __name__ == '__main__':
    get_example_pypi_app_data(pkgname='excel-list-transform',
                              page_fname='test/test_pypkg_recdep/elt_pkg.pkl',
                              raw_fname='test/test_pypkg_recdep/elt_raw.pkl')
