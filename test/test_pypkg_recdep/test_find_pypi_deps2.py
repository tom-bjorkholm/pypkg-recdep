#! /usr/local/bin/python3
"""Test finding dependencies in PyPI."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

from copy import deepcopy
from typing import Optional, NamedTuple
from itertools import cycle
from enum import IntEnum, auto
import pickle
import shutil
import pytest
from pypi_simple import ProjectPage, DistributionPackage, \
    NoMetadataError, NoSuchProjectError
from packaging.version import Version
from packaging.requirements import Requirement
from pypkg_recdep.pkg_info import PkgKey, PkgInfo, create_pkginfo
from pypkg_recdep.find_pypi_deps import set_pkginfo_from_raw, \
    get_environment, get_best_pkg, NoMatchingPackage


def compare_to(expected: dict[str, Optional[str | list]]) -> PkgInfo:
    """Get a dict for comparison."""
    ret = create_pkginfo(key=PkgKey(name='a', version='0.0'))
    for key, value in expected.items():
        assert key in ret
        ret[key] = value
    return ret


@pytest.mark.parametrize('raw,res',
                         [({}, {}),
                          ({'license': ''}, {}),
                          ({'metadata_version': '2.2',
                            'license': 'mit',
                            'project_urls': {'stars': 'http://a.com',
                                             'Source': 'git://a.com'},
                            'home_page': 'http://b.a.com',
                            'maintainer': 'Mr Fix',
                            'requires_dist': ['bcd', 'efg']},
                           {'metadata_version': Version('2.2'),
                            'license': 'MIT',
                            'project_urls': {'stars': 'http://a.com',
                                             'Source': 'git://a.com'},
                            'source_url': 'git://a.com',
                            'homepage': 'http://b.a.com',
                            'maintainer': 'Mr Fix',
                            'dependencies': [Requirement('bcd'),
                                             Requirement('efg')]}),
                          ({'metadata_version': '2.2',
                            'license': 'another MIT',
                            'project_urls': {'stars': 'http://a.com',
                                             'Source': 'git://a.com'},
                            'home_page': 'http://b.a.com',
                            'maintainer': 'Mr Fix',
                            'requires_dist': ['bcd', 'efg']},
                           {'metadata_version': Version('2.2'),
                            'license': 'another MIT',
                            'project_urls': {'stars': 'http://a.com',
                                             'Source': 'git://a.com'},
                            'source_url': 'git://a.com',
                            'homepage': 'http://b.a.com',
                            'maintainer': 'Mr Fix',
                            'dependencies': [Requirement('bcd'),
                                             Requirement('efg')]})])
def test_set_pkginfo_from_raw_ok1(capsys, raw, res):
    """Test OK cases 1 of set_pkginfo_from_raw."""
    expected = compare_to(deepcopy(res))
    info = create_pkginfo(key=PkgKey(name='a', version='0.0'))
    set_pkginfo_from_raw(info=info, raw=deepcopy(raw),
                         pyenv=get_environment(pyversion=Version('3.13')))
    out, err = capsys.readouterr()
    assert len(info) == len(expected)
    for expected_key, expected_value in expected.items():
        print(expected_key)
        assert expected_key in info
        assert expected_value == info[expected_key]
    assert '' == err
    assert '' == out


@pytest.mark.parametrize('surl', ['http://git.local', 'ssh://github.com'])
@pytest.mark.parametrize('skey', ['Source', 'source', 'GitHub', 'github',
                                  'Repository', 'repository', 'Code',
                                  'code', 'Homepage', 'homepage'])
def test_set_pkginfo_from_raw_ok2(capsys, surl, skey):
    """Test OK cases 2 of set_pkginfo_from_raw."""
    raw = {
        'project_urls': {'homepage': 'http://a.com'}
    }
    raw['project_urls'][skey] = surl
    res = {
        'project_urls': {'homepage': 'http://a.com'}
    }
    res['project_urls'][skey] = surl
    res['source_url'] = surl
    expected = compare_to(deepcopy(res))
    info = create_pkginfo(key=PkgKey(name='a', version='0.0'))
    set_pkginfo_from_raw(info=info, raw=deepcopy(raw),
                         pyenv=get_environment(pyversion=Version('3.13')))
    out, err = capsys.readouterr()
    assert len(info) == len(expected)
    for expected_key, expected_value in expected.items():
        print(expected_key)
        assert expected_key in info
        assert expected_value == info[expected_key]
    assert '' == err
    assert '' == out


class MockSpecMeta(NamedTuple):
    """Spec for package and metadata."""

    meta: bool
    version: str
    metaversion: str
    reqs: Optional[list[str]]
    py_req: Optional[str]


class MockSpecPage(NamedTuple):
    """Spec for pages with packages and their metadata."""

    name: str
    base: str
    metas: list[MockSpecMeta]


class LookupWhat(IntEnum):
    """Shall client look up or answer in order."""

    LOOKUP_NONE = auto()
    LOOKUP_NAME = auto()
    LOOKUP_VER = auto()
    LOOKUP_BOTH = auto()


class MockClient1:
    """A mock of PyPISimple client."""

    def __init__(self, spec: list[MockSpecPage],
                 lookup: LookupWhat) -> None:
        """Construct a mocked PyPI´-SImple client."""
        self.spec: list[MockSpecPage] = spec
        self.lookup: LookupWhat = lookup
        self.metaindex = 0
        self.pageindex = len(spec)

    def lookup_page(self, name: str) -> None:
        """Position self page index according to lookup."""
        if self.lookup in (LookupWhat.LOOKUP_NONE, LookupWhat.LOOKUP_VER):
            return
        for idx, pspec in enumerate(self.spec):
            if pspec.name == name:
                self.pageindex = idx
                return
        raise NoSuchProjectError(f'Project {name} not in spec.',
                                 url='http://fake.org')

    def lookup_meta(self, ver: str) -> None:
        """Position self meta index according to lookup."""
        if self.lookup in (LookupWhat.LOOKUP_NONE, LookupWhat.LOOKUP_NAME):
            return
        thispage = self.spec[self.pageindex]
        for idx, mspec in enumerate(thispage.metas):
            if mspec.version == ver:
                self.metaindex = idx
                return
        raise NoMetadataError(f'Version {ver} not in spec.',
                              url='http://fake.org')

    def get_project_page(self, name: str, timeout: float) -> ProjectPage:
        """Get a mocked project page."""
        assert timeout is not None
        assert name is not None
        self.pageindex += 1
        if self.pageindex >= len(self.spec):
            self.pageindex = 0
        self.lookup_page(name)
        thispage = self.spec[self.pageindex]
        self.metaindex = 0
        fname = 'test/test_pypkg_recdep/' + deepcopy(thispage.base) + \
            '_page.pkl'
        with open(file=fname, mode='rb') as file:
            page: ProjectPage = pickle.load(file=file)
            pkgs = deepcopy(page.packages)
            page.packages = []
            page.project = deepcopy(thispage.name)
            for mspec, pkg in zip(thispage.metas, cycle(pkgs)):
                pkg.project = deepcopy(thispage.name)
                pkg.version = deepcopy(mspec.version)
                pkg.has_metadata = deepcopy(mspec.meta)
                pkg.requires_python = deepcopy(mspec.py_req)
                page.packages.append(pkg)
            return page

    @staticmethod
    def rewrite(text: str, key: str, val: list[str]) -> str:
        """Re-write metadata text to have val for key."""
        lines = deepcopy(text).splitlines()
        matchidxs = [i for i, line in enumerate(lines)
                     if line.startswith(key + ': ')]
        first_line = matchidxs[0] if matchidxs else 0
        for idx in reversed(matchidxs):
            del lines[idx]
        for single in reversed(val):
            lines.insert(first_line, key + ': ' + single)
        return '\n'.join(lines) + '\n'

    def get_package_metadata(self, pkg: DistributionPackage,
                             timeout: float) -> str:
        """Get mocked metadata for a package."""
        assert timeout is not None
        self.lookup_meta(pkg.version)
        thispage = self.spec[self.pageindex]
        mspec = thispage.metas[self.metaindex]
        if not mspec.meta:
            return ''
        self.metaindex += 1
        if self.metaindex >= len(mspec):
            self.metaindex = 0
        fname = 'test/test_pypkg_recdep/' + deepcopy(thispage.base) + \
            '_meta.pkl'
        with open(file=fname, mode='rb') as file:
            meta: str = pickle.load(file=file)
            meta = self.rewrite(text=meta, key='Metadata-Version',
                                val=[mspec.metaversion])
            meta = self.rewrite(text=meta, key='Name', val=[thispage.name])
            meta = self.rewrite(text=meta, key='Version', val=[mspec.version])
            meta = self.rewrite(text=meta, key='Requires-Python',
                                val=[mspec.py_req])
            meta = self.rewrite(text=meta, key='Requires-Dist',
                                val=mspec.reqs)
            return meta

    def download_package(self, pkg, path: str, timeout: float) -> None:
        """Get mocked package file for licence text file."""
        assert pkg is not None
        assert timeout is not None
        mockfile = 'pkgtest2.tar.gz'
        if path.endswith(('.whl', '.zip')):
            mockfile = 'pkgtest.zip'
        fromfile = 'test/test_pypkg_recdep/' + mockfile
        shutil.copy(src=fromfile, dst=path)


MT1I = '''Metadata-Version: 2.4
Name: pytest
Version: 9.0.0
Summary:
'''
MT1R1 = '''Metadata-Version: 2.1
Name: pytest
Version: 9.0.0
Summary:
'''
MT1R2 = '''Metadata-Version: 2.4
Name: pytest
Version: 1.0.0
Summary:
'''
MT1R3 = '''Metadata-Version: 2.4
Name: something
Version: 9.0.0
Summary:
'''
MT2I = '''License-File: LICENSE
Requires-Dist: colorama>=0.4; sys_platform == "win32"
Requires-Dist: exceptiongroup>=1; python_version < "3.11"
Requires-Dist: iniconfig>=1.0.1
Requires-Dist: packaging>=22
Requires-Dist: pluggy<2,>=1.5
Requires-Dist: pygments>=2.7.2
Requires-Dist: tomli>=1; python_version < "3.11"
Provides-Extra: dev
Requires-Dist: argcomplete; extra == "dev"
Requires-Dist: attrs>=19.2; extra == "dev"
Requires-Dist: hypothesis>=3.56; extra == "dev"
Requires-Dist: mock; extra == "dev"
Requires-Dist: requests; extra == "dev"
Requires-Dist: setuptools; extra == "dev"
Requires-Dist: xmlschema; extra == "dev"
Dynamic: license-file
'''
MT2R1 = '''License-File: LICENSE
Requires-Dist: abc
Requires-Dist: def >= 1
Provides-Extra: dev
Dynamic: license-file
'''


@pytest.mark.parametrize('txt,key,val,res',
                         [(MT1I, 'Metadata-Version', ['2.1'], MT1R1),
                          (MT1I, 'Version', ['1.0.0'], MT1R2),
                          (MT1I, 'Name', ['something'], MT1R3),
                          (MT2I, 'Requires-Dist', ['abc', 'def >= 1'], MT2R1)
                          ])
def test_mock_rewrite(capsys, txt, key, val, res):
    """Test the mock rewrite function."""
    ret = MockClient1.rewrite(text=txt, key=key, val=val)
    out, err = capsys.readouterr()
    print(ret)
    assert ret == res
    assert '' == out
    assert '' == err


class GetBestPkgRes(NamedTuple):
    """Data to test PkgInfo agains for get_best_pkg."""

    name: str
    version: str
    numreqs: int
    license: Optional[str]
    lic_text: bool


GBP_M1 = [
    MockSpecMeta(meta=True, version='1.0', metaversion='2.1',
                 py_req=' >= 3.10', reqs=['def >= 2', 'fgh >= 1.0.1']),
    MockSpecMeta(meta=True, version='2.0', metaversion='2.4',
                 py_req=' >= 3.12', reqs=['def >= 2', 'fgh >= 1.0.1']),
    MockSpecMeta(meta=True, version='1.5', metaversion='2.2',
                 py_req=' >= 3.11', reqs=['def >= 2', 'fgh >= 1.0.1']),
    MockSpecMeta(meta=False, version='0.9', metaversion='2.0',
                 py_req=' >= 3.8', reqs=['def >= 2', 'fgh >= 1.0.1'])
]
GBP_C1 = [
    MockSpecPage(name='abc', base='elt',
                 metas=GBP_M1)
]

GBP_1R1 = GetBestPkgRes(name='abc', version='2.0', numreqs=2,
                        license='MIT License', lic_text=True)
GBP_1R2 = GetBestPkgRes(name='abc', version='1.5', numreqs=2,
                        license='MIT License', lic_text=True)
GBP_1R3 = GetBestPkgRes(name='abc', version='0.9', numreqs=0,
                        license=None, lic_text=False)


@pytest.mark.parametrize('cspec,req,pyv,metav,res',
                         [(GBP_C1, 'abc >= 0.8', '3.14', None, GBP_1R1),
                          (GBP_C1, 'abc >= 0.8', '3.11', None, GBP_1R2),
                          (GBP_C1, 'abc >= 0.8', '3.9', None, GBP_1R3),
                          (GBP_C1, 'abc >= 0.8', '3.14', '2.2', GBP_1R2)
                          ])
def test_get_best_pkg_ok1(capsys,  # pylint: disable=too-many-arguments,too-many-positional-arguments # noqa: E501
                          cspec, req, pyv, metav, res):
    """Test OK cases of get_best_pkg."""
    mock_client = MockClient1(spec=cspec, lookup=LookupWhat.LOOKUP_BOTH)
    env = get_environment(pyversion=Version(pyv))
    metaversion = Version(metav) if metav is not None else None
    ret: PkgInfo = get_best_pkg(client=mock_client, req=Requirement(req),
                                pyversion=Version(pyv),
                                metaversion=metaversion,
                                pyenv=env)
    out, err = capsys.readouterr()
    assert res.name == ret['key'].name
    assert Version(res.version) == ret['key'].version
    assert res.numreqs == len(ret['dependencies'])
    assert res.license == ret['license']
    if res.lic_text:
        assert ret['license_text'] is not None
        assert len(ret['license_text']) > 0
    else:
        assert ret['license_text'] is None or ret['license_text'] == ''
    assert '' == out
    assert '' == err


GBP_C1N = [
    MockSpecPage(name='abc', base='elt', metas=[])
]


@pytest.mark.parametrize('cspec,req,pyv,excmsg',
                         [(GBP_C1N, 'abc >= 0.8', '3.14', 'No match for abc'),
                          (GBP_C1, 'abc >= 3.8', '3.11',
                           'No match for version abc>=3.8')])
def test_get_best_pkg_nok1(capsys, cspec, req, pyv, excmsg):
    """Test not OK cases of get_best_pkg."""
    mock_client = MockClient1(spec=cspec, lookup=LookupWhat.LOOKUP_BOTH)
    env = get_environment(pyversion=Version(pyv))
    with pytest.raises(NoMatchingPackage) as exc:
        _ = get_best_pkg(client=mock_client, req=Requirement(req),
                         pyversion=Version(pyv),
                         metaversion=None, pyenv=env)
    assert excmsg in str(exc)
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
