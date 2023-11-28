"""Cross-python stdlib shims."""

import os
import typing as t
from contextlib import contextmanager
from pathlib import Path

try:
    from contextlib import chdir as chdir_cm  # type: ignore[attr-defined]
except ImportError:

    @contextmanager  # type: ignore[no-redef]
    def chdir_cm(path: os.PathLike) -> t.Iterator[None]:
        """Temporarily change the current directory, recovering on exit."""
        original_wd = Path.cwd()
        os.chdir(path)
        try:
            yield
        finally:
            os.chdir(original_wd)


try:
    from tomllib import loads as load_toml_from_string
except ImportError:
    from tomli import loads as load_toml_from_string  # type: ignore[no-redef]


__all__ = ("chdir_cm", "load_toml_from_string")  # noqa: WPS410
