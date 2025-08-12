#! /usr/local/bin/python3
"""Test exclude information."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

from copy import deepcopy
from tempfile import TemporaryDirectory
import pytest
from pypkg_recdep.exclude import ExcludeInfo
from pypkg_recdep.pkg_info import PkgKey, create_pkginfo, Pkgs


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


CSVTXT1 = """Code,Name of package,checksum,version
123, abc, a6a7a8, 3.12
234, def, a78a68a9, 4.25
243, abc, b3b2b45b2, 4.13
"""
CSVTXT2 = """Trash, Version in repo, name in repo, checksum
fdsafdas, 1.2.1, ghi, 2bb3b4b5
fdasfaaa, 2.3.4, jkl, 7a8a0a
uoitreuw, 5.6.7, mno, 8723897
qwertyy, 8.9.0, jkl, 90728352
"""
RES1 = {
    'abc': ['3.12', '4.13'],
    'def': ['4.25']
}
RES2 = {
    'ghi': ['1.2.1'],
    'jkl': ['2.3.4', '8.9.0'],
    'mno': ['5.6.7']
}


@pytest.mark.parametrize('csvtxt,res,txt',
                         [(CSVTXT1, RES1, 'some text'),
                          (CSVTXT2, RES2, 'another textß')])
def test_store_parsed_csv_ok1(capsys, csvtxt, res, txt):
    """Test OK cases of ExcludeInfo.store_parsed_csv."""
    excl = ExcludeInfo(txt=deepcopy(txt), csv_filename=None)
    with TemporaryDirectory() as dirname:
        fname = dirname + '/a.csv'
        with open(file=fname, mode='w', encoding='utf-8') as file:
            file.write(csvtxt)
        excl.store_parsed_csv(csv_filename=fname)
        out, err = capsys.readouterr()
        assert excl.exclude_pkgs == res
        assert excl.csv_filename == 'None'
        assert excl.txt == txt
        assert '' == out
        assert '' == err


@pytest.mark.parametrize('csvtxt,res, txt',
                         [(CSVTXT1, RES1, 'init text'),
                          (CSVTXT2, RES2, 'other text')])
def test_construct_exclude_info_ok1(capsys, csvtxt, res, txt):
    """Test OK cases of ExcludeInfo.__init__."""
    with TemporaryDirectory() as dirname:
        fname = dirname + '/a.csv'
        with open(file=fname, mode='w', encoding='utf-8') as file:
            file.write(csvtxt)
        excl = ExcludeInfo(txt=deepcopy(txt), csv_filename=fname)
        out, err = capsys.readouterr()
        assert excl.exclude_pkgs == res
        assert fname == excl.csv_filename
        assert txt == excl.txt
        assert '' == out
        assert '' == err


def test_store_parsed_csv_no_file(capsys):
    """Test error case no file of ExcludeInfo.store_parsed_csv."""
    excl = ExcludeInfo(txt='Some text', csv_filename=None)
    with TemporaryDirectory() as dirname:
        fname = dirname + '/a.csv'
        with pytest.raises(SystemExit):
            excl.store_parsed_csv(csv_filename=fname)
        out, err = capsys.readouterr()
        assert '' == out
        assert 'File with CSV data on packages to exclude details for' in err
        assert 'cannot be found.' in err
        assert f"No such file or directory: '{fname}'" in err


def test_store_parsed_csv_no_name(capsys):
    """Test error case no name column of ExcludeInfo.store_parsed_csv."""
    txt = """hash,version,id
    1b3235432, 1.2.1, ABC-1
    475489982, 2.3.4, DEF-2
    """
    excl = ExcludeInfo(txt='something', csv_filename=None)
    with TemporaryDirectory() as dirname:
        fname = dirname + '/a.csv'
        with open(file=fname, mode='w', encoding='utf-8') as file:
            file.write(txt)
        with pytest.raises(SystemExit):
            excl.store_parsed_csv(csv_filename=fname)
        out, err = capsys.readouterr()
        assert '' == out
        assert 'Did not find "Name" in' in err
        assert f'Unable to parse CSV file {fname}' in err


def test_store_parsed_csv_no_ver(capsys):
    """Test error case no version column of ExcludeInfo.store_parsed_csv."""
    txt = """hash,release,name of it
    1b3235432, 1.2.1, ABC-1
    475489982, 2.3.4, DEF-2
    """
    excl = ExcludeInfo(txt='something', csv_filename=None)
    with TemporaryDirectory() as dirname:
        fname = dirname + '/a.csv'
        with open(file=fname, mode='w', encoding='utf-8') as file:
            file.write(txt)
        with pytest.raises(SystemExit):
            excl.store_parsed_csv(csv_filename=fname)
        out, err = capsys.readouterr()
        assert '' == out
        assert 'Did not find "Version" in' in err
        assert f'Unable to parse CSV file {fname}' in err


def test_excl_info_str(capsys):
    """Test normal case of str on ExcludeInfo."""
    with TemporaryDirectory() as dirname:
        fname = dirname + '/a.csv'
        with open(file=fname, mode='w', encoding='utf-8') as file:
            file.write(CSVTXT1)
        excl = ExcludeInfo(txt=deepcopy('my excludes'), csv_filename=fname)
        out, err = capsys.readouterr()
        assert '' == out
        assert '' == err
        txt = "{'txt': 'my excludes', 'csv_filename': "
        txt += f"'{fname}', 'exclude_pkgs': "
        txt += "{'abc': ['3.12', '4.13'], 'def': ['4.25']}}"
        assert txt == str(excl)


def construct_pkgs(indata: list[tuple[str, str]]) -> Pkgs:
    """Create Pkgs data for use in test from pgkname and version."""
    ret: Pkgs = {}
    for i in indata:
        key = PkgKey(name=deepcopy(i[0]),
                     version=deepcopy(i[1]))
        info = create_pkginfo(key=key)
        ret[key] = info
    return ret


NOEXCL = [
    ('abc', '3.11'),
    ('def', '4.20'),
    ('zyx', '3.12')
]

EXCL = [
    ('abc', '3.12'),
    ('def', '4.25'),
    ('abc', '4.13')
]


@pytest.mark.parametrize('csvtxt,ind,reskeep,resexcl',
                         [(CSVTXT1, {}, {}, {}),
                          (CSVTXT1, construct_pkgs(NOEXCL),
                           construct_pkgs(NOEXCL), {}),
                          (CSVTXT1, construct_pkgs(EXCL), {},
                           construct_pkgs(EXCL)),
                          (CSVTXT1, construct_pkgs(sorted(NOEXCL+EXCL)),
                           construct_pkgs(NOEXCL), construct_pkgs(EXCL))])
def test_split_in_keep_and_excl1(capsys, csvtxt, ind, reskeep, resexcl):
    """Test OK cases of ExcludeInfo.split_in_keep_and_exclude."""
    excl = ExcludeInfo(txt='', csv_filename=None)
    with TemporaryDirectory() as dirname:
        fname = dirname + '/a.csv'
        with open(file=fname, mode='w', encoding='utf-8') as file:
            file.write(csvtxt)
        excl.store_parsed_csv(csv_filename=fname)
    (rkeep, rexcl) = excl.split_in_keep_and_exclude(pkgs=deepcopy(ind))
    out, err = capsys.readouterr()
    assert '' == out
    assert '' == err
    assert resexcl == rexcl
    assert reskeep == rkeep
