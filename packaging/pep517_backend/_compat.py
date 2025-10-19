"""Cross-python stdlib shims."""

import collections.abc as _c  # noqa: WPS111, WPS301
import os
import sys
from contextlib import contextmanager
from pathlib import Path


if sys.version_info >= (3, 11):
    from contextlib import chdir as chdir_cm

    from tomllib import loads as load_toml_from_string
else:
    from tomli import loads as load_toml_from_string

    @contextmanager  # type: ignore[no-redef]
    def chdir_cm(path: 'os.PathLike[str]') -> _c.Iterator[None]:
        """Temporarily change the current directory, recovering on exit."""
        original_wd = Path.cwd()
        os.chdir(path)
        try:  # noqa: WPS505
            yield
        finally:
            os.chdir(original_wd)


__all__ = (  # noqa: WPS410
    'chdir_cm',
    'load_toml_from_string',
)
