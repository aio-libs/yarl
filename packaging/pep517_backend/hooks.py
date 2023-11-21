"""PEP 517 build backend for optionally pre-building Cython."""

from contextlib import suppress as _suppress

from setuptools.build_meta import *  # Re-exporting PEP 517 hooks  # pylint: disable=unused-wildcard-import,wildcard-import  # noqa: E501, F401, F403

# Re-exporting PEP 517 hooks
from ._backend import (  # type: ignore[assignment]  # noqa: WPS436
    build_sdist,
    build_wheel,
    get_requires_for_build_wheel,
    prepare_metadata_for_build_wheel,
)

with _suppress(ImportError):  # Only succeeds w/ setuptools implementing PEP 660
    # Re-exporting PEP 660 hooks
    from ._backend import (  # type: ignore[assignment]  # noqa: WPS436
        build_editable,
        get_requires_for_build_editable,
        prepare_metadata_for_build_editable,
    )
