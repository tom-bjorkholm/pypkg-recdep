"""Repository-specific build specification for common_build_tools."""

from pathlib import Path
from typing import Optional
from build_spec import BuildSpec


def custom_spec() -> Optional[BuildSpec]:
    """Return custom build spec for this repository."""
    return BuildSpec(
        readme_summary_max_skipped=4,
        python_layout_check=False,
        mypy_paths=[Path('test/test_pypkg_recdep')],
    )
