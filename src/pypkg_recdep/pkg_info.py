#! /usr/local/bin/python3
"""Package info types used in other files in pypkg_recdep."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

from typing import TypedDict, Optional, Final
from functools import total_ordering
from packaging.version import Version
from packaging.utils import NormalizedName, canonicalize_name
from packaging.requirements import Requirement


@total_ordering
class PkgKey:
    """Key to a package with name and version."""

    def __init__(self, name: str | NormalizedName,
                 version: str | Version):
        """Create a PkgKey object.

        @param name The name of the package.
        @param version The version of the package.
        """
        self.name: Final[NormalizedName] = canonicalize_name(name)
        self.version: Final[Version] = \
            Version(version) if isinstance(version, str) else version

    def __str__(self) -> str:
        """Convert to string for debug printing."""
        return str(self.__dict__)

    def __hash__(self) -> int:
        """Make hashable so PkgKey can be key in dict."""
        return hash((self.name, self.version))

    def __lt__(self, other: object) -> bool:
        """Test if self is smaller than other."""
        assert isinstance(other, PkgKey)
        if self.name < other.name:
            return True
        if self.name > other.name:
            return False
        return self.version < other.version

    def __eq__(self, other: object) -> bool:
        """Test is self is equal to other."""
        assert isinstance(other, PkgKey)
        return not (self.__lt__(other) or other.__lt__(self))


type Requirements = list[Requirement]


class PkgInfo(TypedDict):
    """Information about a package."""

    key: PkgKey
    metadata_version: Optional[Version]
    license: Optional[str]
    project_urls: dict[str, str]
    homepage: Optional[str]
    source_url: Optional[str]
    maintainer: Optional[str]
    dependencies: Requirements
    license_text: Optional[str]


def create_pkginfo(key: PkgKey) -> PkgInfo:
    """Create PkgInfo object without any information filled in."""
    return PkgInfo(key=key, metadata_version=None, license=None,
                   project_urls={}, homepage=None, source_url=None,
                   maintainer=None, dependencies=[], license_text=None)


type Pkgs = dict[PkgKey, PkgInfo]
