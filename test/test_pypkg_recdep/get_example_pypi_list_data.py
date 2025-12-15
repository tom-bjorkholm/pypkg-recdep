"""Get test data from pypi on package and store to files."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

import sys
from copy import deepcopy
import pickle
from pypi_simple import PyPISimple, IndexPage, \
    ProjectPage
from pypkg_recdep.pkg_info import PkgKey, MockListData


_FNAME = 'test/test_pypkg_recdep/list_data.pkl'


def get_idxpage(client: PyPISimple) -> IndexPage:
    """Get an index page, trimmed to suite our test needs."""
    idx_page: IndexPage = client.get_index_page(timeout=60.0)
    projects: list[str] = deepcopy(idx_page.projects)
    include = ['excel-list-transform', 'jaraco.itertools', 'pytest',
               'mypy', 'pip']
    num_start = 'pytest'
    in_num = False
    num = 20
    count = 0
    for (i, projname) in reversed(list(enumerate(projects))):
        if in_num:
            count += 1
            if count >= num:
                in_num = False
            continue
        if projname == num_start:
            in_num = True
        if projname not in include:
            del projects[i]
    idx_page.projects = projects
    return idx_page


def get_example_pypi_list_data() -> None:
    """Get test data from pypi on package and store to files."""
    with PyPISimple() as client:
        idx_page = get_idxpage(client=client)
        project_pages: dict[str, ProjectPage] = {}
        metas: dict[PkgKey, str] = {}
        for projname in idx_page.projects:
            print(f'Getting project page for {projname}', file=sys.stderr)
            project_pages[projname] = client.get_project_page(projname,
                                                              timeout=30.0)
            for pkg in project_pages[projname].packages:
                if pkg.has_metadata:
                    meta = client.get_package_metadata(pkg, timeout=30.0)
                    metas[PkgKey(pkg.project, pkg.version)] = meta
        mock_list_data = MockListData(idx_page=idx_page,
                                      project_pages=project_pages,
                                      metas=metas)
        with open(file=_FNAME, mode='wb') as file:
            pickle.dump(mock_list_data, file=file,
                        protocol=pickle.HIGHEST_PROTOCOL)
        print(f'Wrote {len(idx_page.projects)} projects to {_FNAME}',
              file=sys.stderr)


def load_example_pypi_list_data() -> MockListData:
    """Load example pypi list data from file."""
    with open(file=_FNAME, mode='rb') as file:
        mlist: MockListData = pickle.load(file=file)
        assert isinstance(mlist, MockListData)
        return mlist
    raise FileNotFoundError(f'File {_FNAME} not found')


if __name__ == '__main__':
    get_example_pypi_list_data()
    example: MockListData = load_example_pypi_list_data()
    assert len(example.idx_page.projects) >= 20
    assert len(example.project_pages) >= 20
    assert len(example.metas) >= 20
    assert 'excel-list-transform' in example.project_pages
