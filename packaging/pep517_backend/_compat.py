"""Cross-python stdlib shims."""

from contextlib import chdir as chdir_cm
from tomllib import loads as load_toml_from_string


__all__ = (  # noqa: WPS410
    'chdir_cm',
    'load_toml_from_string',
)
