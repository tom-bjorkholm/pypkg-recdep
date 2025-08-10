#! /usr/local/bin/python3
"""Test exclude information."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

from copy import deepcopy
import pytest
from pypkg_recdep.exclude import ExcludeInfo


@pytest.mark.parametrize('lst,starts,res',
                         [(['abc', 'bbc', 'cbc', 'BBD'], 'BB', 'bbc')])
def test_find_first_like_ok1(capsys, lst, starts, res):
    """Test OK cases of _find_first_like."""
    ret = ExcludeInfo._find_first_like(lst=deepcopy(lst),  # pylint: disable=protected-access # noqa: E501
                                       starts_with=deepcopy(starts))
    out, err = capsys.readouterr()
    assert ret == res
    assert '' == out
    assert '' == err


@pytest.mark.parametrize('lst,starts,msgs',
                         [(['abc', 'bbc', 'cbc', 'BBD'], 'dc',
                           ['Did not find "dc" in'])])
def test_find_first_like_nok1(capsys, lst, starts, msgs):
    """Test not OK cases of _find_first_like."""
    with pytest.raises(ValueError) as exc:
        _ = ExcludeInfo._find_first_like(lst=deepcopy(lst),  # pylint: disable=protected-access # noqa: E501
                                         starts_with=deepcopy(starts))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    for msg in msgs:
        assert msg in str(exc)


@pytest.mark.parametrize('tostore,res',
                         [([('ab', '1.2.4'),
                            ('de', '3.4.5'),
                            ('ab', '6.7.8'),
                            ('ab', '1.2.4')],
                           {'ab': ['1.2.4', '6.7.8'],
                            'de': ['3.4.5']})])
def test_store_pkg_ver(capsys, tostore, res):
    """Test OK cases of ExcludeInfo.store_pkg_ver."""
    exi = ExcludeInfo(txt='some text', csv_filename=None)
    for i in tostore:
        exi.store_pkg_ver(pkg=i[0], version=i[1])
        out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert exi.exclude_pkgs == res
