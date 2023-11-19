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


__all__ = ("chdir_cm",)  # noqa: WPS410
