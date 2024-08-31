import os
import sys

__all__ = ("cached_property",)


NO_EXTENSIONS = bool(os.environ.get("YARL_NO_EXTENSIONS"))  # type: bool
if sys.implementation.name != "cpython":
    NO_EXTENSIONS = True


if not NO_EXTENSIONS:  # pragma: no branch
    try:
        from ._helpers_c import cached_property

        cached_property_c = cached_property
    except ImportError:  # pragma: no cover
        from ._helpers_py import cached_property  # type: ignore[assignment]

        cached_property_py = cached_property
else:
    from ._helpers_py import cached_property  # type: ignore[assignment]

    cached_property_py = cached_property
