#! /usr/local/bin/python3
"""Test printing dependency information."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

from copy import deepcopy
from tempfile import TemporaryDirectory
from io import StringIO
import pytest
from packaging.requirements import Requirement
from packaging.version import Version
from test_find_pypi_deps2 import MockClient1, LookupWhat, \
    create_test_pkg_spec
from pypkg_recdep.print_deps import print_fulfilling_pkg, \
    print_one_pkg_short, print_one_pkg, print_purl, print_deps, \
    print_rec_deps
from pypkg_recdep.pkg_info import PkgKey, PkgInfo, create_pkginfo, Pkgs
from pypkg_recdep.exclude import ExcludeInfo


# pylint: disable=too-many-arguments,too-many-positional-arguments
def create_test_pkg(name: str, version: str,
                    metadata_version: str = '2.1',
                    license_name: str = 'MIT',
                    homepage: str = 'http://example.com',
                    maintainer: str = 'Test Maintainer',
                    source_url: str = 'http://github.com/test',
                    project_urls: dict = None,
                    dependencies: list = None,
                    license_text: str = None) -> PkgInfo:
    """Create a test package with given properties."""
    key = PkgKey(name=name, version=version)
    info = create_pkginfo(key=key)
    info['metadata_version'] = Version(metadata_version)
    info['license'] = license_name
    info['homepage'] = homepage
    info['maintainer'] = maintainer
    info['source_url'] = source_url
    if project_urls:
        info['project_urls'] = deepcopy(project_urls)
    if dependencies:
        info['dependencies'] = [Requirement(d) for d in dependencies]
    if license_text:
        info['license_text'] = license_text
    return info


@pytest.mark.parametrize('req_str,all_deps,expected_out',
                         [('pytest>=9.0', {}, 'No matching package'),
                          ('pytest>=9.0',
                           {PkgKey('pytest', '9.0.0'):
                            create_pkginfo(PkgKey('pytest', '9.0.0'))},
                           'pytest version: 9.0.0'),
                          ('mylib<2.0',
                           {PkgKey('mylib', '1.5.0'):
                            create_pkginfo(PkgKey('mylib', '1.5.0'))},
                           'mylib version: 1.5.0')])
def test_print_fulfilling_pkg_ok1(capsys, req_str, all_deps,
                                  expected_out):
    """Test OK cases of print_fulfilling_pkg."""
    req = Requirement(req_str)
    file = StringIO()
    print_fulfilling_pkg(file=file, req=req, all_deps=deepcopy(all_deps))
    output = file.getvalue()
    assert expected_out in output
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize(
    'name,version,metadata_version,expected_lines',
    [('test-pkg', '1.0.0', '2.1',
      ['- test-pkg', 'Version: 1.0.0', 'Metadata version: 2.1']),
     ('my-lib', '2.3.4', '2.4',
      ['- my-lib', 'Version: 2.3.4', 'Metadata version: 2.4'])])
def test_print_one_pkg_short_ok1(capsys, name, version, metadata_version,
                                 expected_lines):
    """Test OK cases of print_one_pkg_short."""
    pkg = create_test_pkg(name=name, version=version,
                          metadata_version=metadata_version)
    key = PkgKey(name=name, version=version)
    all_deps: Pkgs = {key: pkg}
    file = StringIO()
    print_one_pkg_short(file=file, pkg=key, data=pkg, all_deps=all_deps)
    output = file.getvalue()
    for line in expected_lines:
        assert line in output
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


def test_print_one_pkg_short_with_urls(capsys):
    """Test print_one_pkg_short with project URLs."""
    pkg = create_test_pkg(
        name='test-pkg', version='1.0.0',
        project_urls={'Homepage': 'http://example.com',
                      'Source': 'http://github.com/test'})
    key = PkgKey(name='test-pkg', version='1.0.0')
    all_deps: Pkgs = {key: pkg}
    file = StringIO()
    print_one_pkg_short(file=file, pkg=key, data=pkg, all_deps=all_deps)
    output = file.getvalue()
    assert 'project URLs:' in output
    assert 'Homepage: http://example.com' in output
    assert 'Source: http://github.com/test' in output
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


def test_print_one_pkg_short_with_deps(capsys):
    """Test print_one_pkg_short with dependencies."""
    dep_pkg = create_test_pkg(name='dep-pkg', version='1.0.0')
    main_pkg = create_test_pkg(
        name='main-pkg', version='2.0.0',
        dependencies=['dep-pkg>=1.0'])
    main_key = PkgKey(name='main-pkg', version='2.0.0')
    dep_key = PkgKey(name='dep-pkg', version='1.0.0')
    all_deps: Pkgs = {main_key: main_pkg, dep_key: dep_pkg}
    file = StringIO()
    print_one_pkg_short(file=file, pkg=main_key, data=main_pkg,
                        all_deps=all_deps)
    output = file.getvalue()
    assert 'Dependencies:' in output
    assert 'dep-pkg' in output
    assert '>=1.0' in output
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('mainpkg,expected_heading',
                         [(True, '## Primary package:'),
                          (False, '###')])
def test_print_one_pkg_ok1(capsys, mainpkg, expected_heading):
    """Test OK cases of print_one_pkg."""
    pkg = create_test_pkg(
        name='test-pkg', version='1.0.0',
        license_text='MIT License\nCopyright 2025')
    key = PkgKey(name='test-pkg', version='1.0.0')
    all_deps: Pkgs = {key: pkg}
    file = StringIO()
    print_one_pkg(file=file, pkg=key, data=pkg, mainpkg=mainpkg,
                  all_deps=all_deps)
    output = file.getvalue()
    assert expected_heading in output
    assert 'test-pkg' in output
    assert 'License text' in output
    assert 'MIT License' in output
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


def test_print_one_pkg_no_license(capsys):
    """Test print_one_pkg without license text."""
    pkg = create_test_pkg(name='test-pkg', version='1.0.0',
                          license_text=None)
    key = PkgKey(name='test-pkg', version='1.0.0')
    all_deps: Pkgs = {key: pkg}
    file = StringIO()
    print_one_pkg(file=file, pkg=key, data=pkg, mainpkg=False,
                  all_deps=all_deps)
    output = file.getvalue()
    assert 'test-pkg' in output
    assert 'License text' not in output
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('name,version,expected',
                         [('test-pkg', '1.0.0', 'pkg:pypi/test-pkg@1.0.0'),
                          ('my-lib', '2.3.4', 'pkg:pypi/my-lib@2.3.4'),
                          ('pkg', None, 'pkg:pypi/pkg')])
def test_print_purl_ok1(capsys, name, version, expected):
    """Test OK cases of print_purl."""
    key = PkgKey(name=name, version=version)
    file = StringIO()
    print_purl(file=file, pkg=key)
    output = file.getvalue().strip()
    assert output == expected
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


def test_print_deps_ok1(capsys):
    """Test OK case of print_deps."""
    main_pkg = create_test_pkg(
        name='main-pkg', version='1.0.0',
        dependencies=['dep1>=1.0', 'dep2'])
    dep1 = create_test_pkg(name='dep1', version='1.0.0')
    dep2 = create_test_pkg(name='dep2', version='2.0.0')
    deps: Pkgs = {
        PkgKey('main-pkg', '1.0.0'): main_pkg,
        PkgKey('dep1', '1.0.0'): dep1,
        PkgKey('dep2', '2.0.0'): dep2
    }
    exclude = ExcludeInfo(txt='excluded', csv_filename=None)
    with TemporaryDirectory() as dirname:
        outfile = dirname + '/output.md'
        ret = print_deps(deps=deepcopy(deps), outfilename=outfile,
                         purls=None, exclude=exclude)
        assert ret == 0
        with open(outfile, 'r', encoding='utf8') as file:
            content = file.read()
        assert '# Package dependency information for main-pkg' in content
        assert '## Primary package: main-pkg' in content
        assert 'dep1' in content
        assert 'dep2' in content
        assert '(End of document.)' in content
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


def test_print_deps_with_purls(capsys):
    """Test print_deps with purls file."""
    main_pkg = create_test_pkg(name='main-pkg', version='1.0.0')
    dep1 = create_test_pkg(name='dep1', version='1.0.0')
    deps: Pkgs = {
        PkgKey('main-pkg', '1.0.0'): main_pkg,
        PkgKey('dep1', '1.0.0'): dep1
    }
    exclude = ExcludeInfo(txt='excluded', csv_filename=None)
    with TemporaryDirectory() as dirname:
        outfile = dirname + '/output.md'
        purls_file = dirname + '/purls.txt'
        ret = print_deps(deps=deepcopy(deps), outfilename=outfile,
                         purls=purls_file, exclude=exclude)
        assert ret == 0
        with open(purls_file, 'r', encoding='utf8') as file:
            purl_content = file.read()
        assert 'pkg:pypi/dep1@1.0.0' in purl_content
        assert 'pkg:pypi/main-pkg@1.0.0' in purl_content
    out, _ = capsys.readouterr()
    assert '' == out


def test_print_deps_with_exclusions(capsys):
    """Test print_deps with excluded packages."""
    main_pkg = create_test_pkg(name='main-pkg', version='1.0.0',
                               dependencies=['dep1', 'excluded-pkg'])
    dep1 = create_test_pkg(name='dep1', version='1.0.0')
    excluded_pkg = create_test_pkg(name='excluded-pkg', version='1.0.0')
    deps: Pkgs = {
        PkgKey('main-pkg', '1.0.0'): main_pkg,
        PkgKey('dep1', '1.0.0'): dep1,
        PkgKey('excluded-pkg', '1.0.0'): excluded_pkg
    }
    with TemporaryDirectory() as dirname:
        # Create CSV file with exclusions
        csv_file = dirname + '/exclusions.csv'
        with open(csv_file, 'w', encoding='utf8') as f:
            f.write('name,version\n')
            f.write('excluded-pkg,1.0.0\n')
        exclude = ExcludeInfo(txt='in standard library',
                              csv_filename=csv_file)
        outfile = dirname + '/output.md'
        ret = print_deps(deps=deepcopy(deps), outfilename=outfile,
                         purls=None, exclude=exclude)
        assert ret == 0
        with open(outfile, 'r', encoding='utf8') as file:
            content = file.read()
        assert 'Also depends on packages' in content
        assert 'in standard library' in content
        assert 'excluded-pkg' in content
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


def test_print_rec_deps_with_mock(capsys, monkeypatch):
    """Test print_rec_deps with mocked resolve_all_dependencies."""
    main_pkg = create_test_pkg(name='test-app', version='1.0.0',
                               dependencies=['dep1'])
    dep1 = create_test_pkg(name='dep1', version='1.0.0')
    mock_deps: Pkgs = {
        PkgKey('test-app', '1.0.0'): main_pkg,
        PkgKey('dep1', '1.0.0'): dep1
    }

    def mock_resolve(root_package, python_version, max_metadata_version):
        """Mock resolve_all_dependencies."""
        assert root_package == 'test-app'
        assert python_version == '3.13'
        assert max_metadata_version == '2.4'
        return deepcopy(mock_deps)

    monkeypatch.setattr(
        'pypkg_recdep.print_deps.resolve_all_dependencies',
        mock_resolve)
    exclude = ExcludeInfo(txt='excluded', csv_filename=None)
    with TemporaryDirectory() as dirname:
        outfile = dirname + '/output.md'
        ret = print_rec_deps(app_name='test-app', metadata_max='2.4',
                             python_ver='3.13', outfilename=outfile,
                             purls=None, exclude=exclude)
        assert ret == 0
        with open(outfile, 'r', encoding='utf8') as file:
            content = file.read()
        assert 'test-app' in content
        assert 'dep1' in content
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


def test_print_rec_deps_with_mockclient1(capsys, monkeypatch):
    """Test print_rec_deps with MockClient1."""
    spec = create_test_pkg_spec()

    def mock_pypisimple():
        """Return MockClient1."""
        return MockClient1(spec=deepcopy(spec),
                           lookup=LookupWhat.LOOKUP_NAME)

    monkeypatch.setattr('pypkg_recdep.find_pypi_deps.PyPISimple',
                        mock_pypisimple)
    exclude = ExcludeInfo(txt='excluded', csv_filename=None)
    with TemporaryDirectory() as dirname:
        outfile = dirname + '/output.md'
        ret = print_rec_deps(app_name='test-pkg', metadata_max='2.4',
                             python_ver='3.13', outfilename=outfile,
                             purls=None, exclude=exclude)
        assert ret == 0
        with open(outfile, 'r', encoding='utf8') as file:
            content = file.read()
        assert 'test-pkg' in content
        assert 'packaging' in content
        assert '(End of document.)' in content
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


def test_print_deps_only_excluded(capsys):
    """Test print_deps when all dependencies are excluded."""
    main_pkg = create_test_pkg(name='main-pkg', version='1.0.0',
                               dependencies=['stdlib-pkg'])
    stdlib_pkg = create_test_pkg(name='stdlib-pkg', version='1.0.0')
    deps: Pkgs = {
        PkgKey('main-pkg', '1.0.0'): main_pkg,
        PkgKey('stdlib-pkg', '1.0.0'): stdlib_pkg
    }
    with TemporaryDirectory() as dirname:
        # Create CSV file with exclusions
        csv_file = dirname + '/exclusions.csv'
        with open(csv_file, 'w', encoding='utf8') as f:
            f.write('name,version\n')
            f.write('stdlib-pkg,1.0.0\n')
        exclude = ExcludeInfo(txt='in standard library',
                              csv_filename=csv_file)
        outfile = dirname + '/output.md'
        ret = print_deps(deps=deepcopy(deps), outfilename=outfile,
                         purls=None, exclude=exclude)
        assert ret == 0
        with open(outfile, 'r', encoding='utf8') as file:
            content = file.read()
        assert 'main-pkg' in content
        assert 'Also depends on packages in standard library' in content
        assert 'stdlib-pkg' in content
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


def test_print_one_pkg_short_all_fields(capsys):
    """Test print_one_pkg_short with all optional fields."""
    pkg = create_test_pkg(
        name='full-pkg', version='3.0.0',
        metadata_version='2.4',
        license_name='Apache-2.0',
        homepage='http://full-pkg.org',
        maintainer='Full Maintainer',
        source_url='http://github.com/full-pkg',
        project_urls={'Docs': 'http://docs.full-pkg.org',
                      'Bugs': 'http://bugs.full-pkg.org'},
        dependencies=['dep1>=2.0', 'dep2<3.0'])
    dep1 = create_test_pkg(name='dep1', version='2.5.0')
    dep2 = create_test_pkg(name='dep2', version='2.0.0')
    key = PkgKey(name='full-pkg', version='3.0.0')
    all_deps: Pkgs = {
        key: pkg,
        PkgKey('dep1', '2.5.0'): dep1,
        PkgKey('dep2', '2.0.0'): dep2
    }
    file = StringIO()
    print_one_pkg_short(file=file, pkg=key, data=pkg, all_deps=all_deps)
    output = file.getvalue()
    assert 'full-pkg' in output
    assert 'Version: 3.0.0' in output
    assert 'Metadata version: 2.4' in output
    assert 'License: Apache-2.0' in output
    assert 'Homepage: http://full-pkg.org' in output
    assert 'Maintainer: Full Maintainer' in output
    assert 'Source URL: http://github.com/full-pkg' in output
    assert 'project URLs:' in output
    assert 'Docs: http://docs.full-pkg.org' in output
    assert 'Dependencies:' in output
    assert 'dep1' in output
    assert 'dep2' in output
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


def test_print_one_pkg_short_dep_no_specifier(capsys):
    """Test print_one_pkg_short with dependency without specifier."""
    dep_pkg = create_test_pkg(name='dep-pkg', version='1.0.0')
    main_pkg = create_test_pkg(
        name='main-pkg', version='2.0.0',
        dependencies=['dep-pkg'])
    main_key = PkgKey(name='main-pkg', version='2.0.0')
    dep_key = PkgKey(name='dep-pkg', version='1.0.0')
    all_deps: Pkgs = {main_key: main_pkg, dep_key: dep_pkg}
    file = StringIO()
    print_one_pkg_short(file=file, pkg=main_key, data=main_pkg,
                        all_deps=all_deps)
    output = file.getvalue()
    assert 'Dependencies:' in output
    assert 'dep-pkg' in output
    # Check that dep-pkg appears without version specifier
    lines = output.split('\n')
    dep_lines = [line for line in lines if 'dep-pkg' in line]
    # Should have at least one line with just dep-pkg (no >=, <, etc.)
    assert any('dep-pkg' in line and '>=' not in line and '<' not in line
               and '==' not in line for line in dep_lines)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


def test_print_deps_only_main_pkg(capsys):
    """Test print_deps when all pkgs excluded (tests line 137)."""
    main_pkg = create_test_pkg(name='main-pkg', version='1.0.0',
                               dependencies=['dep1'])
    dep1 = create_test_pkg(name='dep1', version='1.0.0')
    deps: Pkgs = {
        PkgKey('main-pkg', '1.0.0'): main_pkg,
        PkgKey('dep1', '1.0.0'): dep1
    }
    # Exclude all packages including main pkg to trigger line 137
    with TemporaryDirectory() as dirname:
        csv_file = dirname + '/exclude.csv'
        with open(csv_file, 'w', encoding='utf8') as f:
            f.write('Name,Version\n')
            f.write('main-pkg,1.0.0\n')
            f.write('dep1,1.0.0\n')
        exclude = ExcludeInfo(txt='excluded', csv_filename=csv_file)
        outfile = dirname + '/output.md'
        ret = print_deps(deps=deepcopy(deps), outfilename=outfile,
                         purls=None, exclude=exclude)
        assert ret == 0
        with open(outfile, 'r', encoding='utf8') as file:
            content = file.read()
        assert 'main-pkg' in content
        assert '## Primary package: main-pkg' in content
        # When kept is empty (all pkgs excluded), line 137 is executed
        assert 'Depends only on packages that are {exclude.txt}' in content
        assert 'excluded' in content
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err


def test_print_deps_with_existing_purls_file(capsys):
    """Test print_deps when purls file exists (tests line 159)."""
    main_pkg = create_test_pkg(name='main-pkg', version='1.0.0')
    dep1 = create_test_pkg(name='dep1', version='1.0.0')
    deps: Pkgs = {
        PkgKey('main-pkg', '1.0.0'): main_pkg,
        PkgKey('dep1', '1.0.0'): dep1
    }
    exclude = ExcludeInfo(txt='excluded', csv_filename=None)
    with TemporaryDirectory() as dirname:
        outfile = dirname + '/output.md'
        purls_file = dirname + '/purls.txt'
        # Create existing purls file
        with open(purls_file, 'w', encoding='utf8') as f:
            f.write('pkg:pypi/existing-pkg@1.0.0\n')
        ret = print_deps(deps=deepcopy(deps), outfilename=outfile,
                         purls=purls_file, exclude=exclude)
        assert ret == 0
        with open(purls_file, 'r', encoding='utf8') as file:
            purl_content = file.read()
        # Should have both existing and new packages
        assert 'pkg:pypi/existing-pkg@1.0.0' in purl_content
        assert 'pkg:pypi/dep1@1.0.0' in purl_content
        assert 'pkg:pypi/main-pkg@1.0.0' in purl_content
        out, err = capsys.readouterr()
        # Should print message that file exists and is appending to it
        assert 'File' in out
        assert 'exists. Appending to it.' in out
        assert purls_file in out
        assert '' == err
