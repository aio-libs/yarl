"""Cross-python stdlib shims."""

import os
import typing as t
from contextlib import contextmanager
from pathlib import Path

# isort: off
try:
    from contextlib import chdir as chdir_cm  # type: ignore[attr-defined, unused-ignore] # noqa: E501
except ImportError:

    @contextmanager  # type: ignore[no-redef, unused-ignore]
    def chdir_cm(path: os.PathLike) -> t.Iterator[None]:
        """Temporarily change the current directory, recovering on exit."""
        original_wd = Path.cwd()
        os.chdir(path)
        try:
            yield
        finally:
            os.chdir(original_wd)


# isort: on


try:
    from tomllib import loads as load_toml_from_string
except ImportError:
    from tomli import loads as load_toml_from_string


__all__ = ("chdir_cm", "load_toml_from_string")  # noqa: WPS410
