#! /usr/local/bin/python3
"""Test finding dependencies in PyPI."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

from copy import deepcopy
from typing import Optional
# from tempfile import TemporaryDirectory
# import shutil
# import pickle
import pytest
from packaging.version import Version
from packaging.requirements import Requirement
from pypkg_recdep.pkg_info import PkgKey, PkgInfo, create_pkginfo
from pypkg_recdep.find_pypi_deps import set_pkginfo_from_raw, \
    get_environment


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
