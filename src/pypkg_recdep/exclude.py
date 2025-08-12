#! /usr/local/bin/python3
"""Information about what packages/version to exclude in listing."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

import csv
import sys
from typing import Optional
from pypkg_recdep.pkg_info import Pkgs


class ExcludeInfo():
    """Information on packages to exclude from list."""

    def __init__(self, txt: str, csv_filename: Optional[str]):
        """Construct and ExcludeInfo object.

        @param txt  A text string describing the reason for excluding these
                    packages. For instance 'already in local server'.
                    This text will be copied to the text in the output file.
        @param csv_filename The name of the CSV file with packages to
                    exclude. Needs to have columns 'name' and 'version'.
        """
        self.txt: str = txt
        self.csv_filename: str = csv_filename if csv_filename else 'None'
        self.exclude_pkgs: dict[str, list[str]] = {}
        if csv_filename:
            assert csv_filename is not None
            self.store_parsed_csv(csv_filename)

    def __str__(self) -> str:
        """Enable ruff printing."""
        return str(self.__dict__)

    def store_pkg_ver(self, pkg: str, version: str) -> None:
        """Store package and version as exclude information.

        @param pkg     Name of package that shall be excluded.
        @param version Version of the package to exclude.
        """
        if pkg in self.exclude_pkgs:
            if version not in self.exclude_pkgs[pkg]:
                self.exclude_pkgs[pkg].append(version)
        else:
            self.exclude_pkgs[pkg] = [version]

    @staticmethod
    def _find_first_like(lst: list[str], starts_with: str) -> str:
        """Find first string in list that is like starts_with.

        @param lst         A list of strings to search in.
        @param starts_with The (prefix) string to search for.
        """
        for elem in lst:
            if elem.lower().strip().startswith(starts_with.lower()):
                return elem
        raise ValueError(f'Did not find "{starts_with}" in: {str(lst)}')

    def store_parsed_csv(self, csv_filename: str) -> None:
        """Parse CSV file into dict from pkg name to list of versions.

        Read package name and package version pairs from from the
        comma separated values file and store the name/version pairs
        in a dict that is internal to the ExcludeInfo object.
        @param csv_filename The file name of the CSV file to read from.
        """
        name_col_name: str = ''
        ver_col_name: str = ''
        try:
            with open(file=csv_filename, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file, dialect='unix')
                for row in reader:
                    if name_col_name == '':  # Determine column names first
                        keys = list(row.keys())
                        name_col_name = self._find_first_like(keys, 'Name')
                        ver_col_name = self._find_first_like(keys, 'Version')
                    self.store_pkg_ver(pkg=row[name_col_name].strip(),
                                       version=row[ver_col_name].strip())
        except FileNotFoundError as exc:
            errmsg = 'File with CSV data on packages to exclude details for '
            errmsg += 'cannot be found.'
            print(f'{errmsg}\n{str(exc)}', file=sys.stderr)
            sys.exit(1)
        except ValueError as exc:
            errmsg = f'Unable to parse CSV file {csv_filename}\n{str(exc)}'
            print(errmsg, file=sys.stderr)
            sys.exit(1)

    def split_in_keep_and_exclude(self, pkgs:  Pkgs) -> tuple[Pkgs, Pkgs]:
        """Sort packages into keep and exclude.

        Take the argument list of packages and separate it into two lists.
        One list for the packages to keep/install and one list for the
        packages to exclude.
        @param pkgs The input list of packages.
        """
        keep: Pkgs = {}
        exclude: Pkgs = {}
        for pkgkey, pkginfo in pkgs.items():
            if pkgkey.name in self.exclude_pkgs:
                if str(pkgkey.version) in self.exclude_pkgs[pkgkey.name]:
                    exclude[pkgkey] = pkginfo
                    continue
            keep[pkgkey] = pkginfo
        return (keep, exclude)
