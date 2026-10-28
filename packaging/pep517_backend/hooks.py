"""PEP 517 build backend for optionally pre-building Cython."""

from contextlib import suppress as _suppress

# Re-exporting PEP 517 hooks
# pylint: disable-next=unused-wildcard-import,wildcard-import
from setuptools.build_meta import *  # noqa: F403, WPS347

# Re-exporting PEP 517 hooks
from ._backend import (  # type: ignore[assignment]
    build_sdist,  # noqa: F401
    build_wheel,  # noqa: F401
    get_requires_for_build_wheel,  # noqa: F401
    prepare_metadata_for_build_wheel,  # noqa: F401
)


with _suppress(
    ImportError,
):  # Only succeeds w/ setuptools implementing PEP 660
    # Re-exporting PEP 660 hooks
    from ._backend import (  # type: ignore[assignment]
        build_editable,  # noqa: F401
        get_requires_for_build_editable,  # noqa: F401
        prepare_metadata_for_build_editable,  # noqa: F401
    )
